# Quick Start Guide

Get up and running with the Gelbooru API Wrapper and Telegram Bot in 5 minutes!

## 🚀 5-Minute Setup

### Step 1: Install Dependencies (1 minute)

```bash
pip install python-telegram-bot requests python-dotenv pydantic
```

### Step 2: Get Your Telegram Bot Token (2 minutes)

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Follow the prompts to create your bot
4. Copy the token you receive

### Step 3: Configure Environment (1 minute)

Create a `.env` file:

```bash
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
```

Replace `your_token_here` with your actual token.

### Step 4: Run the Bot (1 minute)

```bash
python telegram_bot.py
```

You should see:
```
INFO - Starting Gelbooru Telegram Bot...
```

### Step 5: Test It!

1. Open Telegram
2. Search for your bot
3. Send `/start`
4. Try: `/search cat_ears rating:safe`

## 🎯 First Commands to Try

```
/start                          # Welcome message
/help                           # See all commands
/search cat_ears rating:safe    # Search for posts
/settings                       # Open settings menu
/blacklist add glasses          # Add tag to blacklist
/autotags toggle rating:safe    # Enable auto-tag
```

## 📖 Using the API Wrapper

### Quick Example

```python
from gelbooru_api import search_posts

# Search for posts
posts = search_posts(['cat_ears', 'rating:safe'], limit=5)

# Display results
for post in posts:
    print(f"Post #{post.id}: {post.file_url}")
```

### Full Client Example

```python
from gelbooru_api import GelbooruClient

with GelbooruClient() as client:
    # Search posts
    posts = client.posts.search(tags=['1girl', 'solo'], limit=10)
    
    # Search tags
    tags = client.tags.search(name_pattern='cat%', limit=20)
    
    # Get specific post
    post = client.posts.get_by_id(1)
```

## 🔧 Optional: Add Gelbooru API Credentials

For unlimited API access (no rate limits):

1. Create account on [Gelbooru](https://gelbooru.com)
2. Go to [Account Options](https://gelbooru.com/index.php?page=account&s=options)
3. Find your API Key and User ID
4. Add to `.env`:

```env
GELBOORU_API_KEY=your_api_key
GELBOORU_USER_ID=your_user_id
```

## 📚 Next Steps

- Read [README.md](README.md) for complete documentation
- Check [example_usage.py](example_usage.py) for more examples
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

## 🐛 Troubleshooting

**Bot not starting?**
- Check your token in `.env`
- Verify Python version: `python --version` (need 3.8+)
- Install dependencies: `pip install -r requirements.txt`

**Rate limit errors?**
- Add Gelbooru API credentials to `.env`
- Authenticated requests have no limits

**Import errors?**
- Run: `pip install -r requirements.txt`
- Check Python version

## 💡 Tips

1. **Use auto-tags** for tags you always want (like `rating:safe`)
2. **Use blacklist** for tags you never want (like `gore`)
3. **Check /help** for all available commands
4. **Use /settings** for the interactive menu

## 🎉 You're Ready!

Start searching and exploring Gelbooru with your new bot!

For more advanced usage, check out the full documentation in [README.md](README.md).

---

**Happy searching! 🔍**