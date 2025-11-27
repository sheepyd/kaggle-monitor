# Kaggle Competition Monitor

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/jue993/kaggle-monitor)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[中文文档](README_CN.md)

A lightweight, highly configurable automation tool designed for data scientists and algorithm engineers.

It runs in the background (or on a server), periodically scans newly published Kaggle competitions, and filters them based on your configured **keywords** (e.g., `LiDAR`, `Point Cloud`, `CV`, `Financial`, etc.). Once a competition of interest is found, it sends an email notification immediately.

Say goodbye to manual page refreshing and never miss an opportunity to earn medals or prizes!

---

## Features

* **Fully Automated**: Supports 24/7 background operation with configurable check intervals (default: every 4 hours).
* **Docker Support**: Provides `Dockerfile` and `docker-compose` for one-click deployment with isolated environment.
* **Keyword Filtering**: Only pushes competitions in your areas of interest, eliminating irrelevant notifications.
* **Email Notifications**: Supports SMTP protocol (Gmail, Outlook, QQ Mail, 163 Mail, etc.).
* **Secure Configuration**: Manages sensitive information (API Key, email password) through `.env` environment variables.
* **Deduplication**: Intelligently records previously notified competitions to prevent duplicate alerts.

---

## Directory Structure

```text
kaggle-monitor/
├── docker-compose.yml    # Docker orchestration file (recommended)
├── Dockerfile            # Image build file
├── monitor.py            # Core monitoring script
├── requirements.txt      # Python dependencies
├── .env.example          # Configuration template (rename to .env)
├── data/                 # Data persistence directory
│   └── notified_competitions.json  # Notified competition records
└── README.md             # Documentation
```

---

## Quick Start

### Option 1: Docker Deployment (Recommended)

Suitable for deployment on VPS or NAS, one-click startup with isolated environment.

```bash
# 1. Clone the repository
git clone https://github.com/sheepyd/kaggle-monitor.git
cd kaggle-monitor

# 2. Configure environment variables
cp .env.example .env
nano .env  # Edit configuration

# 3. Start the service
docker-compose up -d --build

# 4. View logs
docker-compose logs -f
```

**Common management commands:**

```bash
# Stop service
docker-compose down

# Restart service (required after modifying .env)
docker-compose restart
```

### Option 2: Run with Python Directly

Suitable for local development or environments without Docker.

```bash
# 1. Clone the repository
git clone https://github.com/sheepyd/kaggle-monitor.git
cd kaggle-monitor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
nano .env  # Edit configuration

# 4. Run
python monitor.py
```

*Note: For long-term background running on Linux, use `nohup python monitor.py &` or configure a `systemd` service.*

---

## Configuration Guide (.env)

Refer to the `.env.example` file. Key parameters are explained below:

### 1. Kaggle Authentication (Required)

Go to Kaggle -> Settings -> API -> Create New Token to download `kaggle.json`.

```ini
# Enter directly in .env, no need to mount the json file
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_key_string
```

### 2. Monitoring Settings

```ini
# Keywords separated by commas, case-insensitive
# The script scans competition Title and Description
KEYWORDS=3d,point cloud,lidar,segmentation,transformer,depth

# Check interval (in hours)
CHECK_INTERVAL_HOURS=4
```

### 3. Email Settings (SMTP)

Example for **QQ Mail** (requires enabling SMTP and obtaining authorization code):

```ini
SENDER_EMAIL=123456@qq.com
# Note: Use the "authorization code", not your QQ password
SENDER_PASSWORD=abcdefghijklmn
RECEIVER_EMAIL=your_email@xxx.com
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
```

Example for **Gmail** (requires App Password):

```ini
SENDER_EMAIL=yourname@gmail.com
SENDER_PASSWORD=your_16_digit_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

---

## FAQ

**Q: Docker container time is incorrect, logs show 8 hours difference from current time?**

A: Check if `TZ=Asia/Shanghai` is included in `docker-compose.yml`. The default configuration includes this setting. Ensure your host machine time is correct.

**Q: Startup error `urllib.error.URLError: <urlopen error [Errno 111] Connection refused>`?**

A: This is usually due to network issues preventing connection to the Kaggle API.
- For servers in China, try configuring a proxy. Add `https_proxy=http://IP:PORT` in `.env`.
- If using Docker, ensure the container can access the internet.

**Q: No errors but not receiving emails?**

1. Check logs with `docker-compose logs` to see if there's a "Email sent successfully" message.
2. Check your spam folder, emails might be intercepted.
3. Confirm SMTP port (587 with TLS is recommended).

---

## Contributing

If you have new ideas or find bugs, feel free to submit Issues or Pull Requests!

1. Fork this repository
2. Create a new `Feat_xxx` branch
3. Commit your code
4. Create a Pull Request

---

## License

This project is open-sourced under the [MIT License](LICENSE).
