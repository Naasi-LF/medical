# Gastric Disease Web Agent (FastAPI + RAG)

This project provides a local web intelligent agent for gastric disease Q&A with:

- Web crawler for gastric-related medical pages
- RAG knowledge base (chunk + embedding + vector retrieval)
- DeepSeek chat/reasoning model for answers
- DashScope embedding model (Aliyun compatible mode)
- Hallucination control through retrieval-only grounding and source citations

## 1) Environment setup (uv + requirements.txt)

```bash
uv venv
source .venv/bin/activate
uv pip install -U pip
uv pip install requests beautifulsoup4 lxml trafilatura langchain langchain-community langchain-openai langchain-chroma chromadb python-dotenv basedpyright
uv pip freeze > requirements.txt
```

> As requested, dependency management is done with `requirements.txt` only.

## 2) Configure API keys

Copy env template and fill your keys:

```bash
cp .env.example .env
```

Required values:

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL` (default `https://api.deepseek.com`)
- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL` (default `https://dashscope.aliyuncs.com/compatible-mode/v1`)

## 3) Build knowledge base

Use one command (CLI):

```bash
python main.py prepare --max-pages 120
```

## 4) Web UI (FastAPI + simple frontend)

Run:

```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000
```

Open: `http://127.0.0.1:8000`

The page streams `deepseek-reasoner` reasoning first, then final answer.

## Notes on hallucination reduction

- Retrieval-first: answer is generated from retrieved chunks only
- If context is insufficient, agent explicitly states uncertainty
- Output includes source URLs for auditing
- Medical safety reminder is always included in system instruction

## DashScope proxy note

If your shell has SOCKS proxy variables set (for example `ALL_PROXY=socks://127.0.0.1:10808`), embedding calls may fail. Run commands with proxy vars unset:

```bash
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy python main.py prepare --max-pages 120
```

## Project structure

```text
gastric_agent/
  config.py        # env loading and API config
  data_sources.py  # seed sites and gastric keywords
  crawler.py       # domain-limited medical crawler
  kb_builder.py    # chunking + embeddings + Chroma index
  rag.py           # retrieval + DeepSeek answer generation
web_app.py         # FastAPI backend
web/index.html     # minimal frontend
```
