# TaskFlow 任务管理看板

双模块任务管理系统：日常任务看板（三列拖拽）+ 工作周报（项目工时统计）。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts |
| 后端 | FastAPI + SQLAlchemy + SQLite |
| 认证 | JWT（python-jose）+ bcrypt |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 1. 克隆项目

```bash
git clone https://github.com/LuoQiLong/TaskFlow.git
cd TaskFlow
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（默认端口 8000）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成，启动后访问：`http://localhost:8000/docs`

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认端口 5173）
npm run dev
```

访问 `http://localhost:5173`，注册账号后即可使用。

### 4. 配置说明

后端配置在 `backend/app/config.py`，支持以下环境变量（可选，都有默认值）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TASKFLOW_SECRET_KEY` | `taskflow-dev-key-change-in-production` | JWT 密钥 |
| `TASKFLOW_DATABASE_URL` | `sqlite:///./taskflow.db` | 数据库地址 |

可复制 `backend/.env.example` 为 `backend/.env` 自定义配置。

## 功能模块

### 📋 任务看板
- 三列拖拽（待处理 → 进行中 → 已完成）
- 状态/优先级筛选
- 任务创建/编辑/删除
- 标签管理

### 📆 工作周报
- 项目归类管理（支持颜色标记）
- 任务 + 工单统一管理
- 周/月视图切换
- 工时记录与统计
- 里程碑管理（拖拽排序、进度条）
- 跨周任务工时拆分
- 超期预警

### 📊 数据图表
- 任务状态/优先级分布
- 项目工时排名
- 任务 vs 工单占比
- 标签分布统计
- 超期任务统计
- 周饱和度趋势（40h 基线）
- 任务创建趋势
- 月度工时汇总

## 项目结构

```
TaskFlow/
  README.md
  CLAUDE.md                    # Claude Code 指引
  backend/
    requirements.txt
    DATABASE_SCHEMA.md          # 数据库表结构文档
    app/
      main.py                   # 入口
      config.py                 # 配置
      models/                   # ORM 模型（6 张表）
      schemas/                  # Pydantic 验证
      routers/                  # API 路由（8 个模块）
      middleware/auth.py        # JWT 鉴权
  frontend/
    src/
      api/                      # Axios 接口封装
      stores/                   # Pinia 状态管理
      views/                    # 页面组件
      layout/AppLayout.vue      # 布局框架
      router/                   # 路由配置
```

数据库表结构详见 [`backend/DATABASE_SCHEMA.md`](backend/DATABASE_SCHEMA.md)。

## 生产部署

```bash
# 后端（使用 gunicorn）
cd backend
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

# 前端（构建静态文件）
cd frontend
npm run build
# 将 dist/ 目录部署到 Nginx 或 CDN
```
