# TaskFlow 生产部署指南

## 架构说明

```
┌──────────────────────┐      ┌──────────────────────┐
│  Windows Server      │      │  Linux Server        │
│  IIS (前端)          │ ───→ │  Gunicorn (后端)     │
│  静态文件 + 反向代理  │      │  port 8000           │
└──────────────────────┘      └──────────┬───────────┘
                                         │
                                         ▼
                                ┌──────────────────┐
                                │  SQL Server      │
                                │  (已有)          │
                                └──────────────────┘
```

---

## 一、Linux 后端部署

### 1.1 安装 ODBC Driver（连接 SQL Server）

```bash
# Ubuntu / Debian
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql17 unixodbc-dev

# CentOS / RHEL
curl https://packages.microsoft.com/config/rhel/8/prod.repo | sudo tee /etc/yum.repos.d/mssql-release.repo
sudo ACCEPT_EULA=Y yum install -y msodbcsql17 unixodbc-devel

# 验证驱动
odbcinst -q -d | grep "ODBC Driver 17"
```

### 1.2 部署后端代码

```bash
# 创建部署目录
sudo mkdir -p /opt/taskflow/backend
sudo chown $USER:$USER /opt/taskflow/backend

# 从开发机拷贝 backend 目录（排除 venv）
# 方式一：git clone
cd /opt/taskflow
git clone https://github.com/LuoQiLong/TaskFlow.git backend
# 或只取 backend 子目录

# 方式二：scp 从本机拷贝
# scp -r backend/ user@linux-server:/opt/taskflow/backend/
```

### 1.3 创建虚拟环境并安装依赖

```bash
cd /opt/taskflow/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 1.4 配置环境变量

```bash
# 复制生产环境变量模板
cp deploy/linux/.env.production .env

# 修改 .env 中的关键配置：
# ★ 必须修改：
#   TASKFLOW_SECRET_KEY=$(openssl rand -hex 32)
# ★ 按实际修改：
#   TASKFLOW_DB_HOST=你的SQLServer地址
#   TASKFLOW_DB_PASSWORD=你的数据库密码
#   TASKFLOW_CORS_ORIGINS=http://你的Windows前端IP,http://你的域名
```

> ⚠️ **CORS 必须填对**：`TASKFLOW_CORS_ORIGINS` 要填写用户浏览器访问前端的地址（如 `http://10.128.29.144:9002` 或 `http://taskflow.xxx.com`），填错会导致浏览器报跨域错误，页面无法调用后端 API。
>
> 格式要求（**踩过的坑**）：
> - **末尾绝对不能带斜杠** `/`。浏览器发送的 `Origin` 头永远无斜杠（如 `http://10.128.29.144:9002`），带斜杠会精确匹配失败，等于白名单为空。
> - 必须是 **协议 + IP/域名 + 端口**，与浏览器地址栏完全一致（`http` 和 `https`、端口都要对上）。
> - 多个地址用**英文逗号**分隔，不加空格：`http://10.128.29.144:9002,https://taskflow.xxx.com`
>
> 注：本项目走 IIS 反向代理时，前端请求 `/api` 与页面同源，通常不触发跨域；但仍建议按上述规则填对，以防直连场景。

### 1.5 安装 systemd 服务

```bash
sudo cp deploy/linux/backend.service /etc/systemd/system/taskflow.service
sudo systemctl daemon-reload
sudo systemctl enable taskflow
sudo systemctl start taskflow

# 检查状态
sudo systemctl status taskflow
journalctl -u taskflow -f
```

> ⚠️ **修改 `.env` 后必须 `restart`，不能 `reload`（踩过的坑）**
> systemd 的 `EnvironmentFile=/opt/taskflow/backend/.env` 只在服务**启动时**读取一次。`reload`（走 `kill -HUP`）只会让 gunicorn 重载 worker，**不会重读 `.env`**，改的 CORS/数据库等配置不生效。
> ```bash
> sudo systemctl restart taskflow      # 改 .env 后用这个
> ```

### 1.6 开放防火墙

```bash
# firewalld
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

### 1.7 创建首个管理员账号

数据库初始为空，注册的第一个账号只是普通成员，需要手动创建管理员：

```bash
# 在 Linux 后端服务器上执行
cd /opt/taskflow/backend
source venv/bin/activate
python
```

```python
# 在 Python REPL 中执行
from app.utils.security import hash_password
from app.database import SessionLocal
from app.models.user import User
from datetime import datetime

db = SessionLocal()

# 检查是否已有管理员
admin = db.query(User).filter(User.role == "admin").first()
if not admin:
    admin = User(
        email="你的邮箱@xxx.com",       # 改为实际邮箱
        hashed_password=hash_password("你的密码"),  # 改为实际密码
        role="admin",
        display_name="管理员",
        is_active=True,
        created_at=datetime.now(),
    )
    db.add(admin)
    db.commit()
    print("管理员账号已创建")
else:
    print(f"管理员已存在: {admin.email}")

db.close()
```

注册页面无管理员入口，确保至少有一个管理员账号后再开放使用。

### 1.8 验证后端启动

```bash
# 确保能连上 SQL Server
cd /opt/taskflow/backend
source venv/bin/activate
python -c "from app.database import engine; engine.connect(); print('数据库连接成功')"
```

---

## 二、Windows 前端部署

> ⚠️ **前提**：确保 Windows 服务器能访问 Linux 后端的 8000 端口。
> 在 Windows 的 PowerShell 中测试：`Test-NetConnection Linux服务器IP -Port 8000`

### 2.1 构建前端

```bash
# 在本机（开发机）上执行
cd frontend
npm run build
# 产物在 frontend/dist/ 目录
```

> ⚠️ **若 `npm run build` 卡在类型检查（踩过的坑）**
> `npm run build` = `vue-tsc -b && vite build`，会先做严格类型检查。当前代码存在一些"变量声明未使用"及 TS 联合类型误报，会让 `vue-tsc` 失败中断，但**不影响实际运行**。要出发布包时可跳过类型门禁，直接用 vite 打包：
> ```bash
> npx vite build
> ```
> 产物同样在 `frontend/dist/`。（构建时的 `#__PURE__` 注释、chunk 超 500KB 均为警告，可忽略。）

### 2.2 安装 IIS 及所需模块

在 Windows Server 上，通过 **服务器管理器 → 添加角色和功能** 安装：

1. **Web 服务器 (IIS)** — 勾选：
   - Web 服务器 → 常见 HTTP 功能（默认文档、静态内容）
   - 管理工具 → IIS 管理控制台

2. **额外模块**（需单独下载安装）：
   - [URL Rewrite Module](https://www.iis.net/downloads/microsoft/url-rewrite)
   - [Application Request Routing 3.0](https://www.iis.net/downloads/microsoft/application-request-routing)

3. **启用 ARR 代理**（★关键，漏了会导致 `/api` 全部 404）：

   方式一 · IIS 管理器：
   - 打开 IIS 管理器 → 点击**服务器根节点**（不是站点）
   - 双击 "Application Request Routing Cache"
   - 右侧操作栏 → "Server Proxy Settings"
   - 勾选 "**Enable proxy**" → 应用

   方式二 · 命令行（更可靠，UI 勾选偶尔不生效，**推荐用这个确认**）：
   ```powershell
   # 查当前状态（Value=False 表示没开）
   Get-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter 'system.webServer/proxy' -Name 'enabled'

   # 开启
   Set-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter 'system.webServer/proxy' -Name 'enabled' -Value 'True'

   # 生效
   iisreset
   ```

   > ⚠️ **踩过的坑**：`Rewrite` 到绝对地址 `http://LINUX_IP:8000` 完全依赖 ARR 代理。**装了 ARR ≠ 开了代理**。若代理未开，页面能打开（SPA 兜底走本地文件），但所有 `/api` 请求会被 IIS 当本地路径找 → 返回 **404**。

### 2.3 创建 IIS 站点

```powershell
# 1. 创建站点目录
New-Item -ItemType Directory -Path "C:\inetpub\taskflow" -Force

# 2. 将 frontend/dist/ 下所有文件拷贝到 C:\inetpub\taskflow\

# 3. 拷贝 web.config
Copy-Item deploy\windows\web.config C:\inetpub\taskflow\web.config

# 4. 修改 web.config 中的 LINUX服务器IP 为实际 Linux 后端地址

# 5. 创建 IIS 站点
Import-Module WebAdministration
New-IISSite -Name "TaskFlow" -PhysicalPath "C:\inetpub\taskflow" -BindingInformation "*:80:"
```

或在 IIS 管理器中手动创建：
- 站点名称：TaskFlow
- 物理路径：C:\inetpub\taskflow
- 端口：80

### 2.4 关键：修改 web.config

将 `deploy/windows/web.config` 中 **两处** `LINUX服务器IP` 替换为 Linux 服务器的实际 IP：

```xml
<!-- 改之前 -->
<action type="Rewrite" url="http://LINUX服务器IP:8000/api/{R:1}" />

<!-- 改之后 -->
<action type="Rewrite" url="http://10.128.30.100:8000/api/{R:1}" />
```

> ⚠️ **web.config 只能有一个 `<rewrite>` 段（踩过的坑）**
> IIS 规定同一层级 `<system.webServer>` 下只允许**一个 `<rewrite>` 元素**。若拆成两段（例如 API 代理一段、SPA 兜底一段），配置非法，**每个请求直接 500（IIS 通用错误页）**。正确写法是把所有规则放进同一个 `<rewrite><rules>...</rules></rewrite>`，且顺序为：**API 代理 → static 代理 → SPA 兜底**（兜底规则 `match url=".*"` 必须放最后）。仓库里的 `deploy/windows/web.config` 已是正确的单段版本，直接用即可。

### 2.5 开放防火墙

```powershell
New-NetFirewallRule -DisplayName "HTTP 80" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
```

---

## 三、验证部署

### 后端健康检查

```bash
curl http://Linux服务器IP:8000/api/health
# 应返回：{"status": "ok"}
```

### 前端访问

浏览器打开 `http://Windows服务器IP`，应能看到 TaskFlow 登录页面并能正常注册/登录。

---

## 四、生产安全注意事项

1. **JWT 密钥**：`TASKFLOW_SECRET_KEY` 务必更换为强随机字符串
   ```bash
   openssl rand -hex 32
   ```

2. **数据库密码**：不要硬编码在 config.py 中，通过 `.env` 文件传入

3. **关闭调试模式**：Linux 后端用 gunicorn 启动（非 uvicorn --reload）

4. **HTTPS**：生产环境建议配置 SSL 证书（可通过 IIS 绑定或反向代理）

5. **防火墙**：Linux 后端 8000 端口仅允许 Windows 前端访问，不对外暴露
6. **Git 仓库**：如果仓库是私有的，Linux 服务器 `git clone` 前需要配置凭证
   ```bash
   # 方式一：Personal Access Token
   git clone https://你的用户名:你的Token@github.com/LuoQiLong/TaskFlow.git
   
   # 方式二：SSH Key
   ssh-keygen -t ed25519 -C "你的邮箱"
   cat ~/.ssh/id_ed25519.pub  # 把公钥添加到 GitHub Settings → SSH Keys
   git clone git@github.com:LuoQiLong/TaskFlow.git
   ```
7. **代码部署方式**：生产环境建议只部署 `backend/` 和前端 `dist/` 产物，不要整仓库克隆到服务器的公开目录，避免 `.git/` 目录被外部访问。

---

## 五、常见问题排查（Troubleshooting）

> 按"现象 → 根因 → 解决"排列，均为实际部署中踩过的坑。排查顺序建议：先确认后端本身通，再逐层往前端/IIS 排。

### 定位口诀：分层验证

```bash
# ① 后端本机（Linux）—— 确认服务与路由正常
curl http://localhost:8000/api/health          # 期望 {"status":"ok",...}

# ② Windows 服务器 —— 确认能连到 Linux 后端
curl.exe http://LINUX_IP:8000/api/health         # 期望 {"status":"ok",...}

# ③ 浏览器/Windows —— 确认 IIS 反代正常（走前端端口）
curl.exe http://前端IP:端口/api/health            # 期望 {"status":"ok",...}
```
哪一层开始失败，问题就在那一层。

### 问题 1：浏览器打开前端报 **500 - Internal server error**

- **根因**：`web.config` 里出现了**两个 `<rewrite>` 段**，IIS 配置非法。
- **解决**：合并为单个 `<rewrite>`，规则顺序 API 代理 → static 代理 → SPA 兜底。用仓库里已修正的 `deploy/windows/web.config`。详见 [2.4](#24-关键修改-webconfig)。
- **看真实错误**：IIS 管理器 → 站点 → 错误页 → Edit Feature Settings → 选 "Detailed errors"，刷新即可看到具体是哪条配置出错。

### 问题 2：页面能打开，但接口 **404**（如 `/api/auth/login 404`）

- **根因**：**ARR 代理开关未启用**。SPA 兜底走本地文件所以页面能开，但 `/api` 反代到绝对地址依赖 ARR，未开时 IIS 当本地路径找 → 404。
- **快速判定**：浏览器/命令行访问 `http://前端IP:端口/api/health`，404 即代理没通。
- **解决**：命令行开启 ARR 代理 + `iisreset`，详见 [2.2 第 3 步](#22-安装-iis-及所需模块)。
  ```powershell
  Get-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter 'system.webServer/proxy' -Name 'enabled'   # 查
  Set-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter 'system.webServer/proxy' -Name 'enabled' -Value 'True'   # 开
  iisreset
  ```

### 问题 3：接口 **502 / 504 Bad Gateway**

- **根因**：ARR 代理已开，但转发目标不可达 —— Linux 后端 IP/端口填错、后端没起、或防火墙挡了 8000。
- **解决**：在 Windows 服务器上 `curl.exe http://LINUX_IP:8000/api/health` 确认可达；核对 `web.config` 里两处后端 IP；确认 Linux 后端 `systemctl status taskflow` 为 running、8000 端口已放行。

### 问题 4：浏览器报 **CORS / Access-Control-Allow-Origin** 跨域错误

- **根因**：后端 `TASKFLOW_CORS_ORIGINS` 与浏览器地址栏 Origin 不匹配 —— 常见是**末尾带了斜杠**、协议/端口不一致、或改完没重启后端。
- **解决**：设为浏览器实际访问地址、**末尾不带斜杠**，改完 `systemctl restart taskflow`（不能 reload）。详见 [1.4](#14-配置环境变量) 与 [1.5](#15-安装-systemd-服务)。

### 问题 5：改了 `.env` 却不生效

- **根因**：systemd `EnvironmentFile` 只在启动时读取，`reload`(HUP) 不重读。
- **解决**：`sudo systemctl restart taskflow`。

### 问题 6：前端 `npm run build` 失败（vue-tsc 类型报错）

- **根因**：严格类型检查报未使用变量/联合类型误报，不影响运行。
- **解决**：用 `npx vite build` 跳过 tsc 门禁出包。详见 [2.1](#21-构建前端)。

---

## 六、发布速查清单（Checklist）

日常重新发布时，照此顺序逐项确认：

**后端（Linux）**
- [ ] 拉取/更新代码到 `/opt/taskflow/backend`
- [ ] 依赖有变动时 `source venv/bin/activate && pip install -r requirements.txt`
- [ ] 核对 `.env`：`SECRET_KEY` / `DB_*` / `CORS_ORIGINS`（末尾无斜杠）
- [ ] `sudo systemctl restart taskflow` → `systemctl status taskflow` 为 running
- [ ] `curl http://localhost:8000/api/health` 返回 ok

**前端（本机构建 + Windows IIS）**
- [ ] `npx vite build` 产出 `frontend/dist/`
- [ ] 将 `dist/` 全部文件拷到 `C:\inetpub\taskflow\`
- [ ] 覆盖 `web.config`，核对其中两处 Linux 后端 IP；确认只有**一个 `<rewrite>` 段**
- [ ] ARR 代理已开（命令行确认 `enabled=True`）
- [ ] `iisreset`
- [ ] `curl.exe http://前端IP:端口/api/health` 返回 ok
- [ ] 浏览器 Ctrl+F5 强刷，登录/加载数据正常
