# 胃病智能问答系统 (Gastric Disease Q&A Agent)

基于 RAG + 图记忆 的全栈医疗问答系统，毕业设计项目。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Pinia + Vue Router + Vite |
| 后端 | FastAPI (Python) |
| 数据库 | MongoDB + Neo4j (Docker) |
| 向量库 | ChromaDB (本地) |
| LLM | DeepSeek (chat + reasoner) |
| Embedding | 阿里 DashScope text-embedding-v3 |

## 功能特性

- 用户注册/登录 (JWT 认证)
- 流式对话 (支持 DeepSeek 思维链展示)
- RAG 知识检索 (胃病医学文献)
- 图记忆 (自动提取用户健康信息，量身定制回答)
- 历史记录 (会话管理，消息持久化)

## 项目结构

```text
medical/
├── gastric_agent/          # 核心 AI 模块
│   ├── config.py           # 环境变量配置
│   ├── data_sources.py     # 种子站点和关键词
│   ├── crawler.py          # 医学网页爬虫
│   ├── kb_builder.py       # 分块 + 向量化 + Chroma 索引
│   └── rag.py              # 检索 + DeepSeek 生成回答
├── server/                 # FastAPI 后端
│   ├── app.py              # 主入口, CORS, 路由注册
│   ├── database.py         # MongoDB 连接
│   ├── auth.py             # bcrypt 密码哈希, JWT
│   ├── deps.py             # FastAPI 依赖 (Bearer 认证)
│   ├── models.py           # Pydantic 请求/响应模型
│   ├── graph_memory.py     # 图记忆 (实体提取 + 存储)
│   └── routes/
│       ├── auth.py         # 注册/登录接口
│       ├── chat.py         # 会话 CRUD + 流式聊天
│       └── memory.py       # 图记忆管理接口
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # LoginView, ChatView
│   │   ├── components/     # ChatSidebar, ChatMessage, MemoryPanel
│   │   ├── stores/         # Pinia (auth, chat)
│   │   ├── api.js          # Axios 实例 + JWT 拦截器
│   │   └── router.js       # 路由 + 认证守卫
│   └── vite.config.js      # /api 代理到 8000 端口
├── .env                    # 环境变量 (不提交)
├── .env.example            # 环境变量模板
├── main.py                 # CLI: 爬虫 + 知识库构建
└── requirements.txt        # Python 依赖
```

## 快速开始

本项目提供两种运行方式:

1. 本地开发模式: 前端/后端/数据库分开启动（便于调试）
2. 服务器部署模式: Docker 一体化启动（单端口）

### 方案 A: 本地开发模式（前后端数据库分别启动）

#### A1. 环境准备

```bash
# Python 虚拟环境
uv venv && source .venv/bin/activate

# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..
```

#### A2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY / DASHSCOPE_API_KEY
```

本地开发建议保留:
- `MONGO_URI=mongodb://localhost:27017`
- `NEO4J_URI=bolt://localhost:7687`

#### A3. 单独启动数据库

```bash
# MongoDB
docker run -d --name medical-mongo-local -p 27017:27017 -v mongo_data_local:/data/db mongo:7

# Neo4j
docker run -d --name medical-neo4j-local -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/medical2025 -v neo4j_data_local:/data neo4j:5
```

#### A4. 构建向量库

```bash
python main.py prepare --max-pages 120
```

#### A5. 分别启动后端和前端

终端 1（后端）:
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

终端 2（前端）:
```bash
cd frontend && npm run dev
```

访问:
- 前端: `http://localhost:5173`
- 后端 API: `http://localhost:8000`

---

### 方案 B: 服务器部署模式（Docker 一体化，单端口）

目标: `git pull` 后一条命令拉起前端+后端+MongoDB+Neo4j，对外只暴露 `8000`。

#### B1. 首次部署

```bash
cp .env.example .env
# 编辑 .env 填入 DEEPSEEK_API_KEY / DASHSCOPE_API_KEY
```

```bash
docker compose up -d --build
```

访问:
```text
http://<your-server-ip>:8000
```

#### B2. 日常更新（推荐）

```bash
bash deploy.sh
```

`deploy.sh` 会执行:
1) `git pull`
2) `docker compose up -d --build`
3) `docker compose ps`

也可以指定分支:

```bash
bash deploy.sh main
```

#### B3. 运维命令

```bash
docker compose ps
docker compose logs -f app
docker compose down
```

说明:
- 前端静态文件由 FastAPI 容器内托管（`frontend/dist`）
- MongoDB / Neo4j 仅在 Docker 内网通信
- 本地 `./data` 会挂载到容器 `/app/data`，用于向量库持久化

---

### Linux 安装 Docker + Docker Compose（Ubuntu/Debian）

以下为官方仓库安装方式（推荐）。

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 可选: 免 sudo 使用 docker
sudo usermod -aG docker $USER
newgrp docker

docker --version
docker compose version
```

官方文档:
- https://docs.docker.com/engine/install/ubuntu/
- https://docs.docker.com/compose/install/linux/

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录 (返回 JWT) |
| GET | `/api/chat/conversations` | 获取会话列表 |
| POST | `/api/chat/conversations` | 创建新会话 |
| DELETE | `/api/chat/conversations/{id}` | 删除会话 |
| GET | `/api/chat/conversations/{id}/messages` | 获取消息历史 |
| POST | `/api/chat/stream` | 流式聊天 (NDJSON) |
| GET | `/api/memory` | 获取用户图记忆 |
| POST | `/api/memory/extract` | 手动提取实体 |
| DELETE | `/api/memory/entity/{id}` | 删除实体 |
| DELETE | `/api/memory/relation/{id}` | 删除关系 |

## 防幻觉机制

- 检索优先: 仅基于检索到的文档片段生成回答
- 上下文不足时, 模型明确表示不确定
- 回答附带来源 URL 供核实
- 系统提示词包含医疗安全提醒

## 代理说明

如果终端配置了 SOCKS 代理, embedding 调用可能失败。取消代理后运行:

```bash
env -u ALL_PROXY -u all_proxy -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy python main.py prepare --max-pages 120
```
