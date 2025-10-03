# Gelbooru API Wrapper & Telegram Bot

A comprehensive, modular Python wrapper for the Gelbooru API with an integrated Telegram bot featuring inline button menus, tag blacklisting, and auto-tag toggles.

## 🌟 Features

### API Wrapper
- **Modular Architecture**: Clean separation of concerns with dedicated endpoint handlers
- **Type Safety**: Dataclasses and enums for robust type checking
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Rate Limiting**: Built-in retry logic and rate limit detection
- **Authentication Support**: Optional API key authentication for unlimited requests
- **Context Manager**: Automatic resource cleanup with context manager support

### Telegram Bot
- **Inline Keyboard Menus**: Intuitive button-based navigation
- **Tag Blacklist**: Automatically exclude unwanted tags from searches
- **Auto-tag Toggles**: Enable/disable tags that are automatically added to every search
- **Settings Persistence**: User preferences saved automatically in JSON format
- **Search Filtering**: Advanced filtering with blacklist and auto-tag support
- **User-friendly Commands**: Simple command interface for all features

## 📋 Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## 🚀 Installation

### 1. Clone or Download

```bash
# Create project directory
mkdir gelbooru-bot
cd gelbooru-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required for Telegram bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional but recommended for Gelbooru API (removes rate limits)
GELBOORU_API_KEY=your_gelbooru_api_key_here
GELBOORU_USER_ID=your_gelbooru_user_id_here
```

#### Getting Credentials

**Telegram Bot Token:**
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Copy the token provided

**Gelbooru API Credentials (Optional):**
1. Create an account on [Gelbooru](https://gelbooru.com)
2. Go to [Account Options](https://gelbooru.com/index.php?page=account&s=options)
3. Find your API Key and User ID

## 📖 Usage

### API Wrapper

#### Basic Usage

```python
from gelbooru_api import GelbooruClient, search_posts

# Quick search without authentication
posts = search_posts(['cat_ears', 'rating:safe'], limit=10)

for post in posts:
    print(f"Post #{post.id}: {post.file_url}")
```

#### Authenticated Search

```python
from gelbooru_api import GelbooruClient

# Create authenticated client (no rate limits)
client = GelbooruClient(
    api_key='your_api_key',
    user_id='your_user_id'
)

try:
    # Search with multiple tags
    posts = client.posts.search(
        tags=['1girl', 'solo', 'rating:safe'],
        limit=20
    )
    
    for post in posts:
        print(f"Post #{post.id}: Score {post.score}")
        
finally:
    client.close()
```

#### Using Context Manager

```python
from gelbooru_api import GelbooruClient

# Automatic cleanup with context manager
with GelbooruClient() as client:
    posts = client.posts.search(tags=['cat_ears'], limit=10)
    
    # Filter posts
    high_score = [p for p in posts if p.score >= 10]
    print(f"Found {len(high_score)} high-score posts")
```

#### Advanced Filtering

```python
with GelbooruClient() as client:
    # Complex tag query
    posts = client.posts.search(
        tags=[
            'cat_ears',
            'green_eyes',
            '-glasses',      # Exclude glasses
            'rating:safe',
            'score:>=10'     # Minimum score
        ],
        limit=50
    )
    
    # Custom blacklist filtering
    blacklist = ['school_uniform', 'hat']
    filtered = [p for p in posts if not p.has_any_tag(blacklist)]
    
    print(f"After filtering: {len(filtered)} posts")
```

#### Tag Search

```python
with GelbooruClient() as client:
    # Search tags with wildcard
    tags = client.tags.search(name_pattern='cat%', limit=20)
    
    for tag in tags:
        print(f"{tag.name}: {tag.count} posts")
    
    # Get specific tag info
    tag = client.tags.get_by_name('cat_ears')
    if tag:
        print(f"Tag ID: {tag.id}, Count: {tag.count}")
```

#### User Search

```python
with GelbooruClient() as client:
    users = client.users.search(name_pattern='admin%', limit=10)
    
    for user in users:
        print(f"{user.name} (ID: {user.id})")
```

### Telegram Bot

#### Starting the Bot

```bash
python telegram_bot.py
```

#### Bot Commands

**Basic Commands:**
- `/start` - Welcome message and introduction
- `/help` - Detailed help and command reference
- `/search <tags>` - Search for posts with specified tags
- `/settings` - Open settings menu with inline buttons

**Settings Commands:**
- `/blacklist` - Manage tag blacklist
  - `/blacklist` - View current blacklist
  - `/blacklist add <tag>` - Add tag to blacklist
  - `/blacklist remove <tag>` - Remove tag from blacklist
  - `/blacklist clear` - Clear entire blacklist

- `/autotags` - Manage auto-tag toggles
  - `/autotags` - View current auto-tags
  - `/autotags toggle <tag>` - Enable/disable auto-tag

#### Example Bot Usage

**Search with tags:**
```
/search cat_ears rating:safe
```

**Add to blacklist:**
```
/blacklist add school_uniform
/blacklist add glasses
```

**Enable auto-tag:**
```
/autotags toggle rating:safe
```

Now all searches will automatically exclude `school_uniform` and `glasses`, and include `rating:safe`.

**Search with filters applied:**
```
/search cat_ears green_eyes
```
This search will automatically:
- Exclude blacklisted tags (school_uniform, glasses)
- Include auto-tags (rating:safe)

#### Inline Button Menus

The `/settings` command opens an interactive menu with buttons:

- **🚫 Manage Blacklist** - View and manage blacklisted tags
- **🏷️ Manage Auto-tags** - View and manage auto-tags
- **📊 View Stats** - See your settings statistics
- **🔄 Reset Settings** - Clear all settings (with confirmation)

## 🏗️ Architecture

### API Wrapper Design

```
GelbooruClient
├── BaseClient (HTTP handling, auth, rate limiting)
├── PostsEndpoint (post search and retrieval)
├── TagsEndpoint (tag search and info)
├── UsersEndpoint (user search)
└── CommentsEndpoint (comment retrieval)
```

**Key Design Principles:**
1. **Separation of Concerns**: Each endpoint has its own handler class
2. **Type Safety**: Dataclasses for all API responses
3. **Error Handling**: Custom exceptions for different error types
4. **Extensibility**: Easy to add new endpoints or features
5. **Maintainability**: Clear code structure with comprehensive documentation

### Telegram Bot Design

```
GelbooruBot
├── SettingsManager (user preferences persistence)
├── PostFilter (blacklist and filtering logic)
├── Command Handlers (user commands)
└── Callback Handlers (inline button interactions)
```

**Key Features:**
1. **Modular Settings**: JSON-based settings storage
2. **Inline Keyboards**: Button-based navigation
3. **Persistent State**: Settings saved automatically
4. **Extensible**: Easy to add new commands and features

## 📁 Project Structure

```
gelbooru-bot/
├── gelbooru_api.py          # API wrapper implementation
├── telegram_bot.py          # Telegram bot implementation
├── example_usage.py         # Usage examples and demonstrations
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your actual credentials (create this)
├── user_settings.json      # Bot user settings (auto-generated)
└── README.md              # This file
```

## 🔧 Configuration

### API Wrapper Configuration

```python
client = GelbooruClient(
    api_key='your_api_key',      # Optional, removes rate limits
    user_id='your_user_id',      # Optional, required with api_key
    timeout=30                    # Request timeout in seconds
)
```

### Bot Configuration

Edit `.env` file:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token

# Optional (recommended for better rate limits)
GELBOORU_API_KEY=your_api_key
GELBOORU_USER_ID=your_user_id
```

## 🎯 Use Cases

### Use Case 1: Content Curation

```python
with GelbooruClient() as client:
    # Find high-quality safe content
    posts = client.posts.search(
        tags=['rating:safe', 'score:>=20', '1girl'],
        limit=100
    )
    
    # Filter by dimensions
    hd_posts = [p for p in posts if p.width >= 1920]
    
    # Save URLs
    with open('curated_content.txt', 'w') as f:
        for post in hd_posts:
            f.write(f"{post.file_url}\n")
```

### Use Case 2: Tag Analysis

```python
with GelbooruClient() as client:
    # Find popular cat-related tags
    tags = client.tags.search(name_pattern='cat%', limit=100)
    
    # Sort by popularity
    popular = sorted(tags, key=lambda t: t.count, reverse=True)
    
    print("Top 10 cat tags:")
    for i, tag in enumerate(popular[:10], 1):
        print(f"{i}. {tag.name}: {tag.count:,} posts")
```

### Use Case 3: Automated Monitoring

```python
import time

with GelbooruClient(api_key='key', user_id='id') as client:
    last_id = 0
    
    while True:
        # Check for new posts
        posts = client.posts.search(tags=['new_tag'], limit=10)
        
        new_posts = [p for p in posts if p.id > last_id]
        
        if new_posts:
            print(f"Found {len(new_posts)} new posts")
            last_id = max(p.id for p in new_posts)
        
        time.sleep(300)  # Check every 5 minutes
```

## 🧪 Testing

Run the example usage script to test all features:

```bash
python example_usage.py
```

This will demonstrate:
- Basic searches
- Authenticated searches
- Advanced filtering
- Tag operations
- User searches
- Error handling
- And more...

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Keep credentials private
2. **Use environment variables** - Don't hardcode credentials
3. **Rotate API keys** - Change keys periodically
4. **Limit bot permissions** - Only grant necessary Telegram permissions
5. **Validate user input** - Always sanitize user-provided data

## 🐛 Troubleshooting

### Common Issues

**Rate Limit Errors:**
- Solution: Add API key and user ID to `.env` file
- Authenticated requests have no rate limits

**Bot Not Responding:**
- Check if bot token is correct
- Verify bot is running (`python telegram_bot.py`)
- Check internet connection

**Import Errors:**
- Run `pip install -r requirements.txt`
- Verify Python version (3.8+)

**Search Returns No Results:**
- Check tag spelling
- Try broader search terms
- Verify tags exist on Gelbooru

## 📚 API Reference

### GelbooruClient

Main client class for API access.

**Methods:**
- `posts.search(tags, limit, page)` - Search for posts
- `posts.get_by_id(post_id)` - Get specific post
- `tags.search(name, name_pattern, limit)` - Search tags
- `tags.get_by_name(name)` - Get specific tag
- `users.search(name, name_pattern, limit)` - Search users
- `comments.get_by_post_id(post_id)` - Get post comments

### Post Object

**Properties:**
- `id` - Post ID
- `tags` - Space-separated tag string
- `tag_list` - Tags as list
- `rating` - Content rating
- `score` - Post score
- `width`, `height` - Dimensions
- `file_url` - Full image URL
- `preview_url` - Preview image URL
- `source` - Original source URL

**Methods:**
- `has_tag(tag)` - Check if post has tag
- `has_any_tag(tags)` - Check if post has any of the tags

## 🤝 Contributing

This is a complete, production-ready implementation. To extend:

1. **Add new API endpoints**: Create new endpoint classes in `gelbooru_api.py`
2. **Add bot features**: Extend command handlers in `telegram_bot.py`
3. **Improve filtering**: Enhance `PostFilter` class
4. **Add analytics**: Track usage statistics

## 📄 License

This project is provided as-is for educational and personal use.

## 🙏 Acknowledgments

- Gelbooru API for providing the data access
- python-telegram-bot library for Telegram integration
- NinjaTech AI for development

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review example usage scripts
3. Consult Gelbooru API documentation: https://gelbooru.com/index.php?page=help

## 🚀 Future Enhancements

Potential additions:
- [ ] Async API support with aiohttp
- [ ] Caching layer for frequently accessed data
- [ ] Advanced analytics and statistics
- [ ] Web dashboard for bot management
- [ ] Multi-language support
- [ ] Image download and management
- [ ] Scheduled searches and notifications
- [ ] Integration with other booru sites

---

**Built with ❤️ by NinjaTech AI**