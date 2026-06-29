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
#   TASKFLOW_CORS_ORIGINS=http://你的Windows前端IP
```

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

### 1.6 开放防火墙

```bash
# firewalld
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

---

## 二、Windows 前端部署

### 2.1 构建前端

```bash
# 在本机（开发机）上执行
cd frontend
npm run build
# 产物在 frontend/dist/ 目录
```

### 2.2 安装 IIS 及所需模块

在 Windows Server 上，通过 **服务器管理器 → 添加角色和功能** 安装：

1. **Web 服务器 (IIS)** — 勾选：
   - Web 服务器 → 常见 HTTP 功能（默认文档、静态内容）
   - 管理工具 → IIS 管理控制台

2. **额外模块**（需单独下载安装）：
   - [URL Rewrite Module](https://www.iis.net/downloads/microsoft/url-rewrite)
   - [Application Request Routing 3.0](https://www.iis.net/downloads/microsoft/application-request-routing)

3. **启用 ARR 代理**：
   - 打开 IIS 管理器 → 点击服务器根节点
   - 双击 "Application Request Routing Cache"
   - 右侧操作栏 → "Server Proxy Settings"
   - 勾选 "**Enable proxy**" → 应用

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
