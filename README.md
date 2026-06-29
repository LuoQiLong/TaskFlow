# TaskFlow 任务管理看板

双模块任务管理系统：日常任务看板（三列拖拽）+ 工作周报（项目工时统计）。支持多人协作、角色权限、管理员视角切换。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts + Tiptap + xlsx-js-style |
| 后端 | FastAPI + SQLAlchemy + SQL Server |
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

后端配置在 `backend/app/config.py`，支持以下环境变量。启动时会自动加载 `backend/.env` 文件（如存在），系统环境变量优先级更高。

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TASKFLOW_SECRET_KEY` | `taskflow-dev-key-change-in-production` | JWT 密钥 |
| `TASKFLOW_DB_HOST` | `localhost` | 数据库服务器地址 |
| `TASKFLOW_DB_PORT` | — | 数据库端口（可选） |
| `TASKFLOW_DB_USER` | — | 数据库用户名 |
| `TASKFLOW_DB_PASSWORD` | — | 数据库密码 |
| `TASKFLOW_DB_NAME` | `taskflow` | 数据库名称 |
| `TASKFLOW_DB_DRIVER` | `ODBC Driver 17 for SQL Server` | ODBC 驱动 |
| `TASKFLOW_SMTP_HOST` | `smtp.qq.com` | 邮件服务器 |
| `TASKFLOW_SMTP_PORT` | `587` | 邮件端口 |
| `TASKFLOW_SMTP_USER` | — | 发件邮箱（不填则邮件功能不可用） |
| `TASKFLOW_SMTP_PASSWORD` | — | 邮箱授权码 |
| `TASKFLOW_CORS_ORIGINS` | `localhost:5173` | CORS 来源（逗号分隔） |

复制 `backend/.env.example` 为 `backend/.env`，填入实际数据库和邮件配置即可。

## 功能模块

### 📋 任务看板
- 三列拖拽（待处理 → 进行中 → 已完成）
- **富文本编辑器**：支持加粗/斜体/颜色/表格/图片粘贴上传/待办列表
- **文件附件**：拖拽/点击上传，文件列表管理
- 状态/优先级/标签/日期/超期筛选 + 排序
- 任务创建/编辑/删除/归档
- 归档任务抽屉（可恢复/永久删除）

### 📆 工作周报
- 项目归类管理（支持颜色标记）
- 任务 + 工单统一管理
- **富文本编辑器**：支持加粗/斜体/颜色/表格/图片粘贴上传/待办列表
- **文件附件**：拖拽/点击上传，文件列表管理
- 周/月视图切换（自定义胶囊按钮）
- 任务搜索（标题 + 描述模糊搜索）
- 工时记录与统计
- 里程碑管理（拖拽排序、🚩进度条、手动/系统锁定）
- **跨周任务**：自定义每周工时分配、独立完成/撤销、周度列放置
- 超期预警
- **Excel 导出**：含样式的工作项导出

### 👤 用户系统
- 邮箱注册/登录（JWT + bcrypt）
- 忘记/重置密码（QQ 邮箱发送）
- 个人设置页（头像裁剪上传、显示名、改密码）
- 管理员角色（手动在数据库指定）
- 管理员视角切换（自己 / 全部用户 / 指定用户）
- 用户管理页（搜索、角色编辑、启用/禁用、重置密码、删除）
- 暗色模式

### 📊 数据图表
- 任务状态/优先级分布
- 项目工时排名
- 任务 vs 工单占比
- 标签分布统计
- 超期任务统计
- 周饱和度趋势（40h 基线、可自定义）
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
      database.py               # 数据库连接
      models/                   # ORM 模型（7 张表）
      schemas/                  # Pydantic 验证
      routers/                  # API 路由（10 个模块）
      middleware/auth.py        # JWT 鉴权 + 管理员权限
      utils/                    # 安全 + 邮件工具
  frontend/
    src/
      api/                      # Axios 接口封装（10 个模块）
      components/               # 共享组件（TiptapEditor）
      stores/                   # Pinia 状态管理（5 个 store）
      views/                    # 页面组件（8 个页面）
      layout/AppLayout.vue      # 布局框架
      router/                   # 路由配置
      types/                    # 共享类型定义
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
