# Deployment Guide

Complete guide for deploying the Gelbooru API Wrapper and Telegram Bot.

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Telegram account
- (Optional) Gelbooru account with API access

## 🚀 Quick Start Deployment

### Step 1: Set Up Python Environment

```bash
# Check Python version
python --version  # Should be 3.8+

# Create project directory
mkdir gelbooru-bot
cd gelbooru-bot

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 3: Configure Credentials

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use any text editor
```

Add your credentials to `.env`:

```env
# Required: Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional but recommended: Get from Gelbooru account settings
GELBOORU_API_KEY=your_api_key_here
GELBOORU_USER_ID=your_user_id_here
```

### Step 4: Test the Setup

```bash
# Test API wrapper
python -c "from gelbooru_api import search_posts; print('API wrapper OK')"

# Test bot import
python -c "from telegram_bot import GelbooruBot; print('Bot module OK')"
```

### Step 5: Run the Bot

```bash
# Start the bot
python telegram_bot.py
```

You should see:
```
INFO - Starting Gelbooru Telegram Bot...
INFO - Application started
```

### Step 6: Test the Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start` command
4. Try a search: `/search cat_ears rating:safe`

## 🖥️ Production Deployment

### Option 1: Linux Server (Recommended)

#### Using systemd Service

1. **Create service file:**

```bash
sudo nano /etc/systemd/system/gelbooru-bot.service
```

2. **Add configuration:**

```ini
[Unit]
Description=Gelbooru Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/gelbooru-bot
Environment="PATH=/path/to/gelbooru-bot/venv/bin"
ExecStart=/path/to/gelbooru-bot/venv/bin/python telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. **Enable and start service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable gelbooru-bot

# Start service
sudo systemctl start gelbooru-bot

# Check status
sudo systemctl status gelbooru-bot

# View logs
sudo journalctl -u gelbooru-bot -f
```

4. **Manage service:**

```bash
# Stop bot
sudo systemctl stop gelbooru-bot

# Restart bot
sudo systemctl restart gelbooru-bot

# Disable auto-start
sudo systemctl disable gelbooru-bot
```

### Option 2: Using Screen (Simple)

```bash
# Install screen
sudo apt-get install screen  # Ubuntu/Debian
sudo yum install screen       # CentOS/RHEL

# Start screen session
screen -S gelbooru-bot

# Run bot
python telegram_bot.py

# Detach from screen: Press Ctrl+A, then D

# Reattach to screen
screen -r gelbooru-bot

# List screens
screen -ls

# Kill screen session
screen -X -S gelbooru-bot quit
```

### Option 3: Using tmux

```bash
# Install tmux
sudo apt-get install tmux  # Ubuntu/Debian

# Start tmux session
tmux new -s gelbooru-bot

# Run bot
python telegram_bot.py

# Detach from tmux: Press Ctrl+B, then D

# Reattach to tmux
tmux attach -t gelbooru-bot

# List sessions
tmux ls

# Kill session
tmux kill-session -t gelbooru-bot
```

### Option 4: Docker Deployment

1. **Create Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY gelbooru_api.py .
COPY telegram_bot.py .

# Create volume for settings
VOLUME /app/data

# Run bot
CMD ["python", "telegram_bot.py"]
```

2. **Create docker-compose.yml:**

```yaml
version: '3.8'

services:
  gelbooru-bot:
    build: .
    container_name: gelbooru-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    environment:
      - PYTHONUNBUFFERED=1
```

3. **Deploy with Docker:**

```bash
# Build image
docker-compose build

# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container
docker-compose restart
```

### Option 5: Cloud Platforms

#### Heroku

1. **Create Procfile:**

```
worker: python telegram_bot.py
```

2. **Create runtime.txt:**

```
python-3.11.0
```

3. **Deploy:**

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-bot-name

# Set environment variables
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set GELBOORU_API_KEY=your_key
heroku config:set GELBOORU_USER_ID=your_id

# Deploy
git push heroku main

# Scale worker
heroku ps:scale worker=1

# View logs
heroku logs --tail
```

#### AWS EC2

1. **Launch EC2 instance** (Ubuntu 22.04 recommended)
2. **Connect via SSH**
3. **Follow Linux Server deployment steps above**

#### DigitalOcean Droplet

1. **Create droplet** (Ubuntu 22.04)
2. **Connect via SSH**
3. **Follow Linux Server deployment steps above**

## 🔧 Configuration Management

### Environment Variables

Create `.env` file with all required variables:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_token_here

# Gelbooru API (Optional)
GELBOORU_API_KEY=your_api_key
GELBOORU_USER_ID=your_user_id

# Optional: Logging level
LOG_LEVEL=INFO

# Optional: Settings file location
SETTINGS_FILE=user_settings.json
```

### Settings File Location

By default, user settings are stored in `user_settings.json` in the working directory.

To change location, modify `telegram_bot.py`:

```python
self.settings_manager = SettingsManager(
    settings_file="/path/to/custom/settings.json"
)
```

## 📊 Monitoring

### Log Files

Configure logging in `telegram_bot.py`:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

### Health Checks

Add health check endpoint (optional):

```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

# Run in separate thread
import threading
server = HTTPServer(('', 8080), HealthCheckHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
```

### Monitoring Tools

- **Uptime monitoring**: UptimeRobot, Pingdom
- **Log aggregation**: Papertrail, Loggly
- **Error tracking**: Sentry
- **Metrics**: Prometheus + Grafana

## 🔒 Security Best Practices

### 1. Secure Credentials

```bash
# Set proper file permissions
chmod 600 .env

# Never commit .env to git
echo ".env" >> .gitignore
```

### 2. Use Secrets Management

For production, use proper secrets management:

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

### 3. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw enable
```

### 4. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
pip install --upgrade -r requirements.txt
```

### 5. Backup Settings

```bash
# Backup user settings regularly
cp user_settings.json user_settings.backup.json

# Or use automated backup
0 0 * * * cp /path/to/user_settings.json /path/to/backups/settings_$(date +\%Y\%m\%d).json
```

## 🐛 Troubleshooting

### Bot Not Starting

**Check logs:**
```bash
# If using systemd
sudo journalctl -u gelbooru-bot -n 50

# If using screen/tmux
# Reattach and check output
```

**Common issues:**
- Missing dependencies: `pip install -r requirements.txt`
- Invalid token: Check `.env` file
- Port already in use: Kill existing process

### Bot Not Responding

**Check bot status:**
```bash
# If using systemd
sudo systemctl status gelbooru-bot

# Check if process is running
ps aux | grep telegram_bot.py
```

**Restart bot:**
```bash
# If using systemd
sudo systemctl restart gelbooru-bot

# If using screen
screen -X -S gelbooru-bot quit
screen -S gelbooru-bot
python telegram_bot.py
```

### Memory Issues

**Monitor memory usage:**
```bash
# Check memory
free -h

# Check process memory
ps aux --sort=-%mem | head
```

**Optimize:**
- Reduce search limits
- Clear old logs
- Restart bot periodically

### Rate Limiting

**Solution:**
- Add Gelbooru API credentials to `.env`
- Authenticated requests have no rate limits

## 📈 Scaling

### Horizontal Scaling

For multiple bot instances:

1. **Use different bot tokens** for each instance
2. **Separate settings files** for each bot
3. **Load balancing** with reverse proxy

### Vertical Scaling

Increase server resources:
- More RAM for larger caches
- More CPU for faster processing
- SSD for faster I/O

## 🔄 Updates and Maintenance

### Updating the Bot

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt

# Restart bot
sudo systemctl restart gelbooru-bot
```

### Database Migrations

If you modify the settings structure:

```python
# Add migration script
def migrate_settings():
    with open('user_settings.json', 'r') as f:
        data = json.load(f)
    
    # Add new fields
    for user_id, settings in data.items():
        if 'new_field' not in settings:
            settings['new_field'] = default_value
    
    with open('user_settings.json', 'w') as f:
        json.dump(data, f, indent=2)
```

## 📞 Support

For deployment issues:

1. Check logs first
2. Review troubleshooting section
3. Verify all prerequisites
4. Test in development environment first

## ✅ Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Telegram bot token obtained
- [ ] Bot tested locally
- [ ] Production environment prepared
- [ ] Service/process manager configured
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Security measures implemented
- [ ] Documentation reviewed

---

**Ready to deploy!** 🚀