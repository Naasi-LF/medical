from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from .config import get_config


SYSTEM_PROMPT = (
    "你是胃病医学问答助手。必须严格基于检索到的资料回答，"
    "不能编造结论。"
    "\n规则:"
    "\n1) 仅使用提供的上下文信息回答。"
    "\n2) 若上下文和问题主题接近但不完整，先给出保守且有用的建议，再明确不确定点。"
    "\n3) 只有在上下文与问题明显不相关时，才回答: '根据当前知识库资料，我无法确定，请咨询医生或补充更多信息。'"
    "\n3) 输出结构: 结论 + 依据(要点) + 就医提醒。"
    "\n4) 不要提供处方剂量，不替代医生诊疗。"
    "\n5) 若用户问'吃什么药'，可给药物类别与用药注意事项，不给具体剂量与品牌。"
)

GENERAL_GASTRIC_TERMS = {
    "胃",
    "胃炎",
    "胃溃疡",
    "肠胃炎",
    "胃痛",
    "gastritis",
    "gastroenteritis",
    "stomach",
    "gastric",
    "ulcer",
    "h. pylori",
    "helicobacter",
}

NON_TARGET_TERMS = {
    "crohn",
    "colitis",
    "appendic",
    "rectal",
    "colon",
    "anal",
    "hemorrhoid",
    "diverticul",
    "celiac",
    "liver",
    "pancrea",
    "gallbladder",
}

# --- Dynamic retrieval thresholds ---
_ABS_THRESHOLD = 0.3  # Minimum absolute relevance score (filter pure noise)
_REL_RATIO = 0.5  # Keep docs within 50% of best score
_MIN_RESULTS = 2  # Always return at least 2 docs
_MAX_RESULTS = 8  # Never return more than 8 docs


@dataclass
class QAResponse:
    answer: str
    sources: list[str]
    references: list[dict[str, str]]
    retrieved_items: list[dict[str, str]]
    thinking_trace: str


class GastricRAGAgent:
    def __init__(self, persist_dir: str) -> None:
        self.config = get_config()
        self.embeddings = OpenAIEmbeddings(
            model=self.config.dashscope_embedding_model,
            api_key=self.config.dashscope_api_key,
            base_url=self.config.dashscope_base_url,
            check_embedding_ctx_length=False,
            chunk_size=10,
        )
        self.vectordb = Chroma(
            collection_name="gastric_knowledge",
            embedding_function=self.embeddings,
            persist_directory=persist_dir,
        )

    def answer(
        self,
        question: str,
        think_mode: bool = False,
        top_k: int = 5,
        on_thought: Callable[[str], None] | None = None,
        on_reasoning_token: Callable[[str], None] | None = None,
        on_token: Callable[[str], None] | None = None,
        memory_context: str = "",
    ) -> QAResponse:
        if on_thought:
            on_thought("正在理解问题意图...")

        normalized_question = _normalize_question(question)
        docs_with_scores = self.vectordb.similarity_search_with_relevance_scores(
            normalized_question, k=20
        )
        if on_thought:
            on_thought(f"已检索到 {len(docs_with_scores)} 条候选资料，正在筛选...")

        docs = _select_relevant_docs(normalized_question, docs_with_scores)
        if on_thought:
            on_thought(f"已筛选出 {len(docs)} 条高相关资料（动态阈值）。")

        if not docs:
            return QAResponse(
                answer="根据当前知识库资料，我无法确定，请咨询医生或补充更多信息。",
                sources=[],
                references=[],
                retrieved_items=[],
                thinking_trace="",
            )

        context_lines: list[str] = []
        retrieved_items: list[dict[str, str]] = []
        for i, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "")
            title = doc.metadata.get("title", "")
            snippet = doc.page_content[:200].replace("\n", " ").strip()
            retrieved_items.append(
                {
                    "idx": str(i),
                    "title": title or "(untitled)",
                    "source": source,
                    "snippet": snippet,
                }
            )
            context_lines.append(
                f"[资料{i}] 标题: {title}\n来源: {source}\n内容: {doc.page_content[:1200]}"
            )

        llm = self._build_llm(think_mode=think_mode)

        user_prompt = (
            f"用户问题: {question}\n\n"
            "以下是检索到的上下文：\n"
            + "\n\n".join(context_lines)
            + "\n\n请直接给出回答，不要在正文中使用任何编号引用（如[1]、[2]），也不要输出URL。"
        )

        system_content = SYSTEM_PROMPT
        if memory_context:
            system_content = (
                SYSTEM_PROMPT
                + "\n\n"
                + memory_context
                + "\n请根据用户个人健康档案给出量身定制的建议。"
            )

        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=user_prompt),
        ]

        if on_thought:
            on_thought("正在生成最终回答...")

        response_text: str
        reasoning_from_model = ""
        if think_mode and on_token:
            response_text, reasoning_from_model = self._stream_reasoner(
                messages=messages,
                on_token=on_token,
                on_reasoning_token=on_reasoning_token,
            )
        elif on_token:
            response_text, reasoning_from_model = self._stream_answer(
                llm=llm,
                messages=messages,
                on_token=on_token,
                on_reasoning_token=on_reasoning_token,
            )
        else:
            response = llm.invoke(messages)
            response_text = _response_text(response.content)
            reasoning_from_model = _extract_reasoning(response)

        cleaned_text = _clean_output_text(response_text)
        cleaned_text = re.sub(r"\[\d+]", "", cleaned_text)
        references, sources = _build_references(retrieved_items)
        thinking_trace = reasoning_from_model
        if think_mode and not thinking_trace:
            thinking_trace = _build_reasoning_fallback(question, retrieved_items)
        return QAResponse(
            answer=cleaned_text,
            sources=sources,
            references=references,
            retrieved_items=retrieved_items,
            thinking_trace=thinking_trace,
        )

    def _build_llm(self, think_mode: bool) -> ChatOpenAI:
        if think_mode:
            return ChatOpenAI(
                model=self.config.deepseek_reasoner_model,
                api_key=self.config.deepseek_api_key,
                base_url=self.config.deepseek_base_url,
            )

        return ChatOpenAI(
            model=self.config.deepseek_chat_model,
            api_key=self.config.deepseek_api_key,
            base_url=self.config.deepseek_base_url,
            temperature=0.1,
        )

    @staticmethod
    def _stream_answer(
        llm: ChatOpenAI,
        messages: list[Any],
        on_token: Callable[[str], None],
        on_reasoning_token: Callable[[str], None] | None = None,
    ) -> tuple[str, str]:
        answer_tokens: list[str] = []
        reasoning_tokens: list[str] = []
        for chunk in llm.stream(messages):
            additional = getattr(chunk, "additional_kwargs", {})
            if isinstance(additional, dict):
                reasoning_piece = additional.get("reasoning_content")
                if isinstance(reasoning_piece, str) and reasoning_piece:
                    cleaned_reasoning = _clean_stream_piece(reasoning_piece)
                    reasoning_tokens.append(cleaned_reasoning)
                    if on_reasoning_token:
                        on_reasoning_token(cleaned_reasoning)

            piece = _response_text(chunk.content)
            if piece:
                cleaned_piece = _clean_stream_piece(piece)
                answer_tokens.append(cleaned_piece)
                on_token(cleaned_piece)

        return "".join(answer_tokens), "".join(reasoning_tokens)

    def _stream_reasoner(
        self,
        messages: list[Any],
        on_token: Callable[[str], None],
        on_reasoning_token: Callable[[str], None] | None = None,
    ) -> tuple[str, str]:
        client = OpenAI(
            api_key=self.config.deepseek_api_key,
            base_url=self.config.deepseek_base_url,
        )
        payload = [_message_to_openai_dict(message) for message in messages]

        stream = client.chat.completions.create(
            model=self.config.deepseek_reasoner_model,
            messages=payload,
            stream=True,
        )

        answer_tokens: list[str] = []
        reasoning_tokens: list[str] = []

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            reasoning_piece = getattr(delta, "reasoning_content", None)
            if isinstance(reasoning_piece, str) and reasoning_piece:
                cleaned_reasoning = _clean_stream_piece(reasoning_piece)
                reasoning_tokens.append(cleaned_reasoning)
                if on_reasoning_token:
                    on_reasoning_token(cleaned_reasoning)

            content_piece = getattr(delta, "content", None)
            if isinstance(content_piece, str) and content_piece:
                cleaned_content = _clean_stream_piece(content_piece)
                answer_tokens.append(cleaned_content)
                on_token(cleaned_content)

        return "".join(answer_tokens), "".join(reasoning_tokens)


def _response_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


def _clean_output_text(text: str) -> str:
    cleaned = text.replace("**", "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _clean_stream_piece(text: str) -> str:
    return text.replace("**", "")


def _extract_reasoning(response: Any) -> str:
    additional_kwargs = getattr(response, "additional_kwargs", {})
    if isinstance(additional_kwargs, dict):
        direct = additional_kwargs.get("reasoning_content")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        reasoning = additional_kwargs.get("reasoning")
        if isinstance(reasoning, str) and reasoning.strip():
            return reasoning.strip()
        if isinstance(reasoning, dict):
            summary = reasoning.get("summary")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()

    content = getattr(response, "content", None)
    if isinstance(content, list):
        traces: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") in {
                "reasoning",
                "reasoning_content",
            }:
                text = block.get("text") or block.get("content")
                if isinstance(text, str) and text.strip():
                    traces.append(text.strip())
        if traces:
            return "\n\n".join(traces)
    return ""


def _build_reasoning_fallback(
    question: str, retrieved_items: list[dict[str, str]]
) -> str:
    lines = [
        "1) 识别问题意图：先判断问题属于胃病定义/症状/诊断/治疗中的哪一类。",
        f"2) 检索证据：基于问题“{question}”检索知识库，当前命中 {len(retrieved_items)} 条相关片段。",
        "3) 交叉核对：优先使用高质量医疗站点来源，过滤不一致或无关信息。",
        "4) 组织答案：输出“结论 + 依据 + 就医提醒”，并附可追溯来源。",
    ]
    if retrieved_items:
        top_titles = [
            item.get("title", "") for item in retrieved_items[:3] if item.get("title")
        ]
        if top_titles:
            lines.append(f"5) 关键证据标题：{'；'.join(top_titles)}")
    return "\n".join(lines)


def _normalize_question(question: str) -> str:
    normalized = re.sub(r"\s+", "", question.strip().lower())
    if not normalized:
        return question
    return normalized


def _select_relevant_docs(
    question: str, docs_with_scores: list[tuple[Any, float]]
) -> list[Any]:
    if not docs_with_scores:
        return []

    question_terms = _extract_terms(question)
    is_general_gastric = bool(question_terms & GENERAL_GASTRIC_TERMS)

    adjusted: list[tuple[float, Any]] = []
    for doc, raw_score in docs_with_scores:
        title = str(doc.metadata.get("title", "")).lower()
        content = str(doc.page_content[:1500]).lower()
        blob = f"{title} {content}"

        score = raw_score

        if is_general_gastric and any(term in blob for term in NON_TARGET_TERMS):
            score *= 0.4

        if any(term in title for term in GENERAL_GASTRIC_TERMS):
            score = min(score * 1.15, 1.0)

        adjusted.append((score, doc))

    adjusted.sort(key=lambda item: item[0], reverse=True)

    if not adjusted:
        return []

    best_score = adjusted[0][0]
    dynamic_threshold = max(_ABS_THRESHOLD, best_score * _REL_RATIO)

    selected = [doc for score, doc in adjusted if score >= dynamic_threshold]

    if len(selected) < _MIN_RESULTS:
        selected = [doc for _, doc in adjusted[:_MIN_RESULTS]]
    if len(selected) > _MAX_RESULTS:
        selected = selected[:_MAX_RESULTS]

    return selected


def _extract_terms(text: str) -> set[str]:
    lowered = text.lower()
    terms: set[str] = set()

    for term in GENERAL_GASTRIC_TERMS | NON_TARGET_TERMS:
        if term in lowered:
            terms.add(term)

    zh_terms = re.findall(r"[\u4e00-\u9fff]{2,6}", lowered)
    terms.update(zh_terms)
    en_terms = re.findall(r"[a-z][a-z\.-]{2,20}", lowered)
    terms.update(en_terms)
    return terms


def _build_references(
    retrieved_items: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[str]]:
    seen: set[str] = set()
    refs: list[dict[str, str]] = []
    idx = 1
    for item in retrieved_items:
        url = item.get("source", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        refs.append({
            "idx": str(idx),
            "title": item.get("title", "").strip() or "(untitled)",
            "source": url,
        })
        idx += 1
    sources = [ref["source"] for ref in refs]
    return refs, sources


def _message_to_openai_dict(message: Any) -> ChatCompletionMessageParam:
    role = getattr(message, "type", "user")
    content = _response_text(getattr(message, "content", ""))

    if role == "system":
        return {"role": "system", "content": content}
    if role == "human":
        return {"role": "user", "content": content}
    if role == "ai":
        return {"role": "assistant", "content": content}
    if role == "assistant":
        return {"role": "assistant", "content": content}
    return {"role": "user", "content": content}
