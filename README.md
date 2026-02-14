# 胃病智能问答系统 (Gastric Disease Q&A Agent)

基于 RAG + 图记忆 的全栈医疗问答系统，毕业设计项目。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Pinia + Vue Router + Vite |
| 后端 | FastAPI (Python) |
| 数据库 | MongoDB (Docker) |
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

### 1. 环境准备

```bash
# Python 虚拟环境
uv venv && source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
pip install pymongo "python-jose[cryptography]"

# 安装前端依赖
cd frontend && npm install && cd ..
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 填入你的 DeepSeek 和 DashScope API Key
```

### 3. 启动 MongoDB

```bash
docker pull mongo:7
docker run -d --name medical-mongo -p 27017:27017 -v mongo_data:/data/db mongo:7
```

### 4. 构建知识库

```bash
python main.py prepare --max-pages 120
```

### 5. 启动服务

终端 1 — 后端:
```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

终端 2 — 前端:
```bash
cd frontend && npm run dev
```

打开浏览器访问: `http://localhost:5173`

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
