import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_chat_model: str
    deepseek_reasoner_model: str
    dashscope_api_key: str
    dashscope_base_url: str
    dashscope_embedding_model: str
    # MongoDB
    mongo_uri: str
    mongo_db_name: str
    # JWT
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    # Neo4j
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str


_cached_config: AppConfig | None = None


def get_config() -> AppConfig:
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    load_dotenv()
    _sanitize_proxy_env_for_openai_clients()

    config = AppConfig(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_chat_model=os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat"),
        deepseek_reasoner_model=os.getenv(
            "DEEPSEEK_REASONER_MODEL", "deepseek-reasoner"
        ),
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
        dashscope_base_url=os.getenv(
            "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ),
        dashscope_embedding_model=os.getenv(
            "DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3"
        ),
        mongo_uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        mongo_db_name=os.getenv("MONGO_DB_NAME", "gastric_agent"),
        jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production-2025"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "1440")),
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "medical2025"),
    )

    missing = []
    if not config.deepseek_api_key:
        missing.append("DEEPSEEK_API_KEY")
    if not config.dashscope_api_key:
        missing.append("DASHSCOPE_API_KEY")
    if missing:
        raise ValueError(
            f"Missing required environment variable(s): {', '.join(missing)}"
        )

    _cached_config = config
    return config


def _sanitize_proxy_env_for_openai_clients() -> None:
    proxy_keys = [
        "ALL_PROXY",
        "all_proxy",
        "HTTP_PROXY",
        "http_proxy",
        "HTTPS_PROXY",
        "https_proxy",
    ]
    for key in proxy_keys:
        value = os.getenv(key)
        if not value:
            continue
        scheme = urlparse(value).scheme.lower()
        if scheme.startswith("socks"):
            os.environ.pop(key, None)
