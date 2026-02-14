"""Graph memory: extract user entities/relations via DeepSeek and store in Neo4j."""

from __future__ import annotations

import json
import re
from typing import Any

from neo4j import GraphDatabase
from openai import OpenAI

from gastric_agent.config import get_config

_driver = None


def _get_driver():
    global _driver
    if _driver is not None:
        return _driver
    cfg = get_config()
    _driver = GraphDatabase.driver(
        cfg.neo4j_uri,
        auth=(cfg.neo4j_user, cfg.neo4j_password),
    )
    with _driver.session() as session:
        session.run("CREATE INDEX IF NOT EXISTS FOR (m:MemoryNode) ON (m.user_id)")
        session.run("CREATE INDEX IF NOT EXISTS FOR (m:MemoryNode) ON (m.name)")
    return _driver


EXTRACT_PROMPT = """\
你是一个医疗信息提取助手。请从用户消息中提取个人健康相关的结构化实体和关系。

需要提取的实体类型:
- age_group: 年龄段 (儿童/青年/中年/老年)
- gender: 性别
- condition: 疾病/症状 (如胃炎、胃溃疡、反酸)
- medication: 正在服用的药物
- allergy: 过敏信息
- habit: 生活习惯 (如吸烟、饮酒、饮食习惯)
- family_history: 家族病史
- preference: 偏好 (如不想吃西药、偏好中医)

输出严格的JSON格式:
{
  "entities": [
    {"type": "condition", "name": "胃炎", "properties": {"severity": "慢性"}}
  ],
  "relations": [
    {"source": "用户", "relation": "患有", "target": "胃炎"}
  ]
}

如果消息中没有可提取的个人健康信息，返回: {"entities": [], "relations": []}
不要编造信息，只提取明确提到的内容。
"""


def extract_entities_from_text(text: str) -> dict[str, list]:
    """Use DeepSeek-chat to extract entities/relations from user text."""
    cfg = get_config()
    client = OpenAI(api_key=cfg.deepseek_api_key, base_url=cfg.deepseek_base_url)

    resp = client.chat.completions.create(
        model=cfg.deepseek_chat_model,
        messages=[
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.0,
    )

    raw = resp.choices[0].message.content or ""

    # Extract JSON from possible markdown code block
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if json_match:
        raw = json_match.group(1)

    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        return {"entities": [], "relations": []}

    return {
        "entities": data.get("entities", []),
        "relations": data.get("relations", []),
    }


def save_user_memory(user_id: str, extracted: dict[str, list]) -> dict[str, int]:
    driver = _get_driver()
    new_entities = 0
    new_relations = 0

    with driver.session() as session:
        for ent in extracted.get("entities", []):
            entity_type = ent.get("type", "unknown")
            entity_name = ent.get("name", "")
            if not entity_name:
                continue

            props_json = json.dumps(ent.get("properties", {}), ensure_ascii=False)
            summary = session.run(
                """
                MERGE (e:MemoryNode {user_id: $uid, name: $name})
                SET e:Entity, e.entity_type = $etype, e.properties = $props
                """,
                uid=user_id,
                name=entity_name,
                etype=entity_type,
                props=props_json,
            ).consume()
            new_entities += summary.counters.nodes_created

        for rel in extracted.get("relations", []):
            source = rel.get("source", "")
            relation = rel.get("relation", "")
            target = rel.get("target", "")
            if not (source and relation and target):
                continue

            summary = session.run(
                """
                MERGE (s:MemoryNode {user_id: $uid, name: $src})
                MERGE (t:MemoryNode {user_id: $uid, name: $tgt})
                MERGE (s)-[r:RELATES_TO {relation: $rel}]->(t)
                """,
                uid=user_id,
                src=source,
                tgt=target,
                rel=relation,
            ).consume()
            new_relations += summary.counters.relationships_created

    return {"new_entities": new_entities, "new_relations": new_relations}


def get_user_memory(user_id: str) -> dict[str, list]:
    driver = _get_driver()
    entities: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []

    with driver.session() as session:
        entity_rows = session.run(
            """
            MATCH (e:Entity {user_id: $uid})
            RETURN elementId(e) AS id, e.entity_type AS entity_type,
                   e.name AS entity_name, e.properties AS properties
            """,
            uid=user_id,
        )
        for row in entity_rows:
            props_raw = row["properties"] or "{}"
            try:
                props = json.loads(props_raw)
            except (json.JSONDecodeError, TypeError):
                props = {}
            entities.append(
                {
                    "id": row["id"],
                    "entity_type": row["entity_type"],
                    "entity_name": row["entity_name"],
                    "properties": props,
                }
            )

        rel_rows = session.run(
            """
            MATCH (s:MemoryNode {user_id: $uid})-[r:RELATES_TO]->(t:MemoryNode)
            RETURN elementId(r) AS id, s.name AS source,
                   r.relation AS relation, t.name AS target
            """,
            uid=user_id,
        )
        for row in rel_rows:
            relations.append(
                {
                    "id": row["id"],
                    "source": row["source"],
                    "relation": row["relation"],
                    "target": row["target"],
                }
            )

    return {"entities": entities, "relations": relations}


def delete_user_entity(user_id: str, entity_id: str) -> bool:
    driver = _get_driver()
    with driver.session() as session:
        summary = session.run(
            """
            MATCH (e:Entity)
            WHERE elementId(e) = $eid AND e.user_id = $uid
            DETACH DELETE e
            """,
            eid=entity_id,
            uid=user_id,
        ).consume()
        return summary.counters.nodes_deleted > 0


def delete_user_relation(user_id: str, relation_id: str) -> bool:
    driver = _get_driver()
    with driver.session() as session:
        summary = session.run(
            """
            MATCH (s:MemoryNode {user_id: $uid})-[r:RELATES_TO]->()
            WHERE elementId(r) = $rid
            DELETE r
            """,
            rid=relation_id,
            uid=user_id,
        ).consume()
        return summary.counters.relationships_deleted > 0


def build_memory_context(user_id: str) -> str:
    """Build a text summary of user's graph memory for injection into prompts."""
    memory = get_user_memory(user_id)

    if not memory["entities"] and not memory["relations"]:
        return ""

    lines = ["[用户个人健康档案]"]

    # Group entities by type
    by_type: dict[str, list[dict]] = {}
    for ent in memory["entities"]:
        t = ent["entity_type"]
        by_type.setdefault(t, []).append(ent)

    type_labels = {
        "age_group": "年龄段",
        "gender": "性别",
        "condition": "疾病/症状",
        "medication": "用药",
        "allergy": "过敏",
        "habit": "生活习惯",
        "family_history": "家族病史",
        "preference": "偏好",
    }

    for t, ents in by_type.items():
        label = type_labels.get(t, t)
        names = [e["entity_name"] for e in ents]
        lines.append(f"- {label}: {', '.join(names)}")

    if memory["relations"]:
        lines.append("关系:")
        for rel in memory["relations"]:
            lines.append(f"  {rel['source']} → {rel['relation']} → {rel['target']}")

    return "\n".join(lines)
