# Kaggle Competition Monitor (Kaggle 竞赛监控器)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/jue993/kaggle-monitor)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个轻量级、高度可配置的自动化监控工具，专为数据科学家和算法工程师设计。

它运行在后台（或服务器上），定期扫描 Kaggle 最新发布的比赛，并根据你设定的**关键词**（如 `LiDAR`, `Point Cloud`, `CV`, `Financial` 等）进行过滤。一旦发现感兴趣的新比赛，立刻通过邮件发送通知。

告别手动刷新页面，不再错过任何一个赚取奖牌或奖金的机会！

---

## 功能特性

* **全自动监控**：支持 7x24 小时后台运行，定频检查（默认每 4 小时）。
* **Docker 支持**：提供 `Dockerfile` 和 `docker-compose`，一键部署，环境隔离。
* **关键词过滤**：只推送你关心的领域，告别无关信息的打扰。
* **邮件通知**：支持 SMTP 协议（Gmail, Outlook, QQ邮箱, 163邮箱等）。
* **安全配置**：通过 `.env` 环境变量管理敏感信息（API Key, 邮箱密码），保护隐私。
* **去重机制**：智能记录已推送过的比赛，防止重复报警。

---

## 目录结构

```text
kaggle-monitor/
├── docker-compose.yml    # Docker 编排文件 (推荐)
├── Dockerfile            # 镜像构建文件
├── monitor.py            # 核心监控脚本
├── requirements.txt      # Python 依赖
├── .env.example          # 配置文件模板 (需重命名为 .env)
├── data/                 # 数据持久化目录
│   └── notified_competitions.json  # 已通知比赛记录
└── README.md             # 说明文档
```

---

## 快速开始 (Docker 部署 - 推荐)

这是最简单、最稳定的部署方式，适合部署在 VPS 或群晖/NAS 上。

### 方式一：使用 Docker Hub 镜像

```bash
# 1. 拉取镜像
docker pull jue993/kaggle-monitor:latest

# 2. 创建配置文件
mkdir kaggle-monitor && cd kaggle-monitor
curl -o .env.example https://raw.githubusercontent.com/sheepyd/kaggle-monitor/main/.env.example
cp .env.example .env
nano .env  # 编辑配置

# 3. 运行容器
docker run -d \
  --name kaggle-monitor \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -e TZ=Asia/Shanghai \
  jue993/kaggle-monitor:latest
```

### 方式二：从源码构建

```bash
# 1. 获取代码
git clone https://github.com/sheepyd/kaggle-monitor.git
cd kaggle-monitor

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置

# 3. 一键启动
docker-compose up -d --build
```

### 常用管理命令

```bash
# 查看运行日志 (确认是否启动成功)
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务 (修改 .env 后需要重启)
docker-compose restart
```

---

## 本地开发 / 传统部署

如果你不想使用 Docker，也可以直接在 Python 环境中运行。

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

同样需要配置 `.env` 文件（同上）。或者，你可以将 Kaggle 的官方认证文件 `kaggle.json` 放入 `~/.kaggle/` 目录下。

### 3. 运行脚本

```bash
python monitor.py
```

*注：若需在 Linux 后台长期运行，建议使用 `nohup` 或配置 `systemd` 服务。*

---

## 配置详解 (.env)

请参考 `.env.example` 文件。以下是关键参数说明：

### 1. Kaggle 认证 (必填)

你需要登录 Kaggle -> Settings -> API -> Create New Token 获取 `kaggle.json`。

```ini
# 直接在 .env 中填入，无需挂载 json 文件
KAGGLE_USERNAME=你的kaggle用户名
KAGGLE_KEY=你的key字符串
```

### 2. 监控设置

```ini
# 关键词用英文逗号分隔，不区分大小写
# 脚本会扫描比赛的 Title 和 Description
KEYWORDS=3d,point cloud,lidar,segmentation,transformer,depth

# 检查频率（单位：小时）
CHECK_INTERVAL_HOURS=4
```

### 3. 邮件发送 (SMTP)

以 **QQ 邮箱**为例（需要开启 SMTP 并获取授权码）：

```ini
SENDER_EMAIL=123456@qq.com
# 注意：这里填的是邮箱的"授权码"，不是QQ密码
SENDER_PASSWORD=abcdefghijklmn
RECEIVER_EMAIL=你的接收邮箱@xxx.com
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
```

以 **Gmail** 为例（需要 App Password）：

```ini
SENDER_EMAIL=yourname@gmail.com
SENDER_PASSWORD=你的16位应用专用密码
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

---

## 常见问题 (FAQ)

**Q: Docker 容器的时间不对，日志显示的时间和当前时间差 8 小时？**

A: 请检查 `docker-compose.yml` 中是否包含 `TZ=Asia/Shanghai`。默认配置已包含此项，确保你的宿主机时间正常。

**Q: 启动报错 `urllib.error.URLError: <urlopen error [Errno 111] Connection refused>`？**

A: 这通常是因为网络问题无法连接 Kaggle API。
- 如果是国内服务器，请尝试配置代理。在 `.env` 中添加 `https_proxy=http://IP:PORT`。
- 如果使用 Docker，请确保容器能访问外网。

**Q: 程序没有报错，但是没有收到邮件？**

1. 检查日志 `docker-compose logs`，看是否有 "邮件发送成功" 的提示。
2. 检查垃圾箱（Spam），邮件可能被拦截。
3. 确认 SMTP 端口（推荐使用 587 端口 + TLS）。

---

## 贡献与支持

如果你有新的想法或发现了 Bug，欢迎提交 Issue 或 Pull Request！

1. Fork 本仓库
2. 新建 `Feat_xxx` 分支
3. 提交代码
4. 新建 Pull Request

---

## License

本项目基于 [MIT License](LICENSE) 开源。
