# VPS Deployment Guide

Bot is deployed on a Hetzner server in Finland running as a systemd service.

## Server Access

```bash
ssh root@YOUR_SERVER_IP
```

## Bot Management

| What | Command |
|---|---|
| Check if bot is running | `systemctl status polybot` |
| Watch live logs | `journalctl -u polybot -f` |
| Stop the bot | `systemctl stop polybot` |
| Start the bot | `systemctl start polybot` |
| Restart the bot | `systemctl restart polybot` |

## Deploy Updates

After pushing new code to GitHub:

```bash
cd /opt/bot && git pull
systemctl restart polybot
```

If you changed `requirements.txt`:

```bash
cd /opt/bot && git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart polybot
```

## File Locations on Server

| What | Path |
|---|---|
| Bot code | `/opt/bot/` |
| Python venv | `/opt/bot/venv/` |
| Environment variables | `/opt/bot/scripts/.env` |
| Systemd service file | `/etc/systemd/system/polybot.service` |

## Edit Environment Variables

```bash
nano /opt/bot/scripts/.env
systemctl restart polybot
```

## Edit Service Config

```bash
nano /etc/systemd/system/polybot.service
systemctl daemon-reload
systemctl restart polybot
```

## Service Config Contents

```ini
[Unit]
Description=Polymarket Copy Trading Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/bot/scripts
ExecStart=/opt/bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

## Rebuild From Scratch

If you ever need to set up a fresh server:

```bash
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv git -y
cd /opt
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git bot
cd bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano scripts/.env          # paste your env vars
cd scripts && ../venv/bin/python main.py   # test it works, Ctrl+C to stop
```

Then create the systemd service (see "Service Config Contents" above) and enable it:

```bash
systemctl daemon-reload
systemctl enable polybot
systemctl start polybot
```

## View Older Logs

```bash
# Last 100 lines
journalctl -u polybot -n 100

# Logs from today
journalctl -u polybot --since today

# Logs from last hour
journalctl -u polybot --since "1 hour ago"
```
