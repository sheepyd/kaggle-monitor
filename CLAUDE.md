# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kaggle Competition Monitor - A Python automation tool that periodically scans Kaggle for new competitions, filters them by configurable keywords, and sends email notifications via SMTP.

## Commands

### Run directly
```bash
pip install -r requirements.txt
python monitor.py
```

### Docker deployment
```bash
docker-compose up -d --build    # Start service
docker-compose logs -f          # View logs
docker-compose down             # Stop service
docker-compose restart          # Restart (after .env changes)
```

## Architecture

Single-file application (`monitor.py`) with this flow:
1. `main()` - Infinite loop with configurable check interval
2. `check_and_notify()` - Orchestrates each check cycle
3. `get_competitions()` - Fetches from Kaggle API via `kaggle` package
4. `filter_competitions()` - Matches against keywords, excludes already-notified
5. `send_email()` - Sends HTML email via SMTP (SSL on port 465, TLS on 587)

Persistence: `data/notified_competitions.json` stores competition IDs to prevent duplicate notifications.

## Configuration

All settings via `.env` file (copy from `.env.example`):
- `KAGGLE_USERNAME`, `KAGGLE_KEY` - Kaggle API credentials
- `KEYWORDS` - Comma-separated filter terms (case-insensitive)
- `CHECK_INTERVAL_HOURS` - Polling frequency
- `SENDER_EMAIL`, `SENDER_PASSWORD`, `RECEIVER_EMAIL` - SMTP auth
- `SMTP_SERVER`, `SMTP_PORT` - Mail server settings

## Dependencies

- `kaggle` - Official Kaggle API client
- `python-dotenv` - Environment variable loading
