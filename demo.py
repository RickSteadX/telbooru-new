"""
Demo Script - Gelbooru API Wrapper & Telegram Bot
==================================================

This script demonstrates the functionality without requiring API credentials.
Shows the code structure and how to use the components.

Author: NinjaTech AI
"""

from gelbooru_api import (
    GelbooruClient,
    Post,
    Tag,
    User,
    Rating,
    SortField,
    SortOrder
)

# Import settings and filter components separately to avoid telegram dependency
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict

@dataclass
class UserSettings:
    """User settings data structure."""
    user_id: int
    blacklist: List[str]
    auto_tags: Dict[str, bool]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSettings':
        return cls(**data)

class SettingsManager:
    """Manages user settings with file-based persistence."""
    
    def __init__(self, settings_file: str = "user_settings.json"):
        self.settings_file = Path(settings_file)
        self.settings: Dict[int, UserSettings] = {}
        self._load_settings()
    
    def _load_settings(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.settings = {
                        int(user_id): UserSettings.from_dict(settings)
                        for user_id, settings in data.items()
                    }
            except Exception:
                self.settings = {}
    
    def _save_settings(self):
        try:
            data = {
                str(user_id): settings.to_dict()
                for user_id, settings in self.settings.items()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def get_settings(self, user_id: int) -> UserSettings:
        if user_id not in self.settings:
            self.settings[user_id] = UserSettings(
                user_id=user_id,
                blacklist=[],
                auto_tags={}
            )
            self._save_settings()
        return self.settings[user_id]
    
    def add_to_blacklist(self, user_id: int, tag: str):
        settings = self.get_settings(user_id)
        if tag not in settings.blacklist:
            settings.blacklist.append(tag)
            self._save_settings()
    
    def remove_from_blacklist(self, user_id: int, tag: str):
        settings = self.get_settings(user_id)
        if tag in settings.blacklist:
            settings.blacklist.remove(tag)
            self._save_settings()
    
    def toggle_auto_tag(self, user_id: int, tag: str) -> bool:
        settings = self.get_settings(user_id)
        current_state = settings.auto_tags.get(tag, False)
        settings.auto_tags[tag] = not current_state
        self._save_settings()
        return settings.auto_tags[tag]
    
    def get_auto_tags(self, user_id: int) -> List[str]:
        settings = self.get_settings(user_id)
        return [tag for tag, enabled in settings.auto_tags.items() if enabled]

class PostFilter:
    """Filters posts based on user settings."""
    
    @staticmethod
    def apply_blacklist(posts: List[Post], blacklist: List[str]) -> List[Post]:
        if not blacklist:
            return posts
        
        blacklist_lower = [tag.lower() for tag in blacklist]
        filtered = []
        
        for post in posts:
            post_tags = [tag.lower() for tag in post.tag_list]
            if not any(bl_tag in post_tags for bl_tag in blacklist_lower):
                filtered.append(post)
        
        return filtered
    
    @staticmethod
    def apply_filters(posts: List[Post], blacklist: List[str], max_results: int = 10) -> List[Post]:
        filtered = PostFilter.apply_blacklist(posts, blacklist)
        return filtered[:max_results]


def demo_api_wrapper_structure():
    """Demonstrate API wrapper structure."""
    print("=" * 60)
    print("API WRAPPER STRUCTURE DEMO")
    print("=" * 60)
    
    print("\n1. Creating a client:")
    print("   client = GelbooruClient(api_key='key', user_id='id')")
    
    print("\n2. Available endpoints:")
    print("   - client.posts.search(tags=['cat_ears'], limit=10)")
    print("   - client.posts.get_by_id(post_id=123)")
    print("   - client.tags.search(name_pattern='cat%')")
    print("   - client.tags.get_by_name('cat_ears')")
    print("   - client.users.search(name='username')")
    print("   - client.comments.get_by_post_id(123)")
    
    print("\n3. Using context manager:")
    print("   with GelbooruClient() as client:")
    print("       posts = client.posts.search(tags=['rating:safe'])")
    
    print("\n4. Data models available:")
    print("   - Post: Complete post information")
    print("   - Tag: Tag metadata and statistics")
    print("   - User: User information")
    
    print("\n5. Error handling:")
    print("   - GelbooruAPIError: Base exception")
    print("   - RateLimitError: Rate limit exceeded")
    print("   - AuthenticationError: Auth failed")


def demo_post_model():
    """Demonstrate Post data model."""
    print("\n" + "=" * 60)
    print("POST DATA MODEL DEMO")
    print("=" * 60)
    
    # Create a sample post
    sample_post = Post(
        id=12345,
        tags="cat_ears green_eyes 1girl solo rating:safe",
        created_at="2024-01-01 12:00:00",
        score=42,
        width=1920,
        height=1080,
        md5="abc123def456",
        directory="images",
        image="sample.jpg",
        rating="safe",
        source="https://example.com",
        change=1234567890,
        owner="user123",
        creator_id=999,
        parent_id=0,
        sample=1,
        preview_height=150,
        preview_width=150,
        file_url="https://example.com/image.jpg",
        sample_url="https://example.com/sample.jpg",
        sample_height=500,
        sample_width=500,
        preview_url="https://example.com/preview.jpg"
    )
    
    print(f"\nSample Post #{sample_post.id}:")
    print(f"  Rating: {sample_post.rating}")
    print(f"  Score: {sample_post.score}")
    print(f"  Dimensions: {sample_post.width}x{sample_post.height}")
    print(f"  Tags: {sample_post.tags}")
    
    print(f"\nTag operations:")
    print(f"  Tag list: {sample_post.tag_list}")
    print(f"  Has 'cat_ears': {sample_post.has_tag('cat_ears')}")
    print(f"  Has 'dog_ears': {sample_post.has_tag('dog_ears')}")
    print(f"  Has any ['cat_ears', 'fox_ears']: {sample_post.has_any_tag(['cat_ears', 'fox_ears'])}")


def demo_settings_manager():
    """Demonstrate Settings Manager."""
    print("\n" + "=" * 60)
    print("SETTINGS MANAGER DEMO")
    print("=" * 60)
    
    # Create settings manager
    manager = SettingsManager(settings_file="demo_settings.json")
    
    # Get settings for a user
    user_id = 123456789
    settings = manager.get_settings(user_id)
    
    print(f"\nUser {user_id} settings:")
    print(f"  Blacklist: {settings.blacklist}")
    print(f"  Auto-tags: {settings.auto_tags}")
    
    # Add to blacklist
    manager.add_to_blacklist(user_id, "glasses")
    manager.add_to_blacklist(user_id, "hat")
    settings = manager.get_settings(user_id)
    print(f"\nAfter adding to blacklist:")
    print(f"  Blacklist: {settings.blacklist}")
    
    # Toggle auto-tags
    manager.toggle_auto_tag(user_id, "rating:safe")
    manager.toggle_auto_tag(user_id, "1girl")
    settings = manager.get_settings(user_id)
    print(f"\nAfter toggling auto-tags:")
    print(f"  Auto-tags: {settings.auto_tags}")
    
    # Get enabled auto-tags
    enabled = manager.get_auto_tags(user_id)
    print(f"  Enabled auto-tags: {enabled}")
    
    # Remove from blacklist
    manager.remove_from_blacklist(user_id, "hat")
    settings = manager.get_settings(user_id)
    print(f"\nAfter removing from blacklist:")
    print(f"  Blacklist: {settings.blacklist}")


def demo_post_filter():
    """Demonstrate Post Filter."""
    print("\n" + "=" * 60)
    print("POST FILTER DEMO")
    print("=" * 60)
    
    # Create sample posts
    posts = [
        Post(
            id=1, tags="cat_ears green_eyes 1girl", created_at="", score=10,
            width=1920, height=1080, md5="", directory="", image="",
            rating="safe", source="", change=0, owner="", creator_id=0,
            parent_id=0, sample=0, preview_height=0, preview_width=0,
            file_url="", sample_url="", sample_height=0, sample_width=0,
            preview_url=""
        ),
        Post(
            id=2, tags="cat_ears glasses blue_eyes", created_at="", score=15,
            width=1920, height=1080, md5="", directory="", image="",
            rating="safe", source="", change=0, owner="", creator_id=0,
            parent_id=0, sample=0, preview_height=0, preview_width=0,
            file_url="", sample_url="", sample_height=0, sample_width=0,
            preview_url=""
        ),
        Post(
            id=3, tags="dog_ears brown_eyes 1girl", created_at="", score=20,
            width=1920, height=1080, md5="", directory="", image="",
            rating="safe", source="", change=0, owner="", creator_id=0,
            parent_id=0, sample=0, preview_height=0, preview_width=0,
            file_url="", sample_url="", sample_height=0, sample_width=0,
            preview_url=""
        ),
    ]
    
    print(f"\nOriginal posts: {len(posts)}")
    for post in posts:
        print(f"  Post #{post.id}: {post.tags}")
    
    # Apply blacklist
    blacklist = ["glasses"]
    filtered = PostFilter.apply_blacklist(posts, blacklist)
    
    print(f"\nAfter blacklist filter (excluding 'glasses'): {len(filtered)}")
    for post in filtered:
        print(f"  Post #{post.id}: {post.tags}")
    
    # Apply all filters
    filtered = PostFilter.apply_filters(posts, blacklist, max_results=2)
    print(f"\nAfter all filters (max 2 results): {len(filtered)}")
    for post in filtered:
        print(f"  Post #{post.id}: {post.tags}")


def demo_bot_commands():
    """Demonstrate bot command structure."""
    print("\n" + "=" * 60)
    print("TELEGRAM BOT COMMANDS DEMO")
    print("=" * 60)
    
    print("\nAvailable commands:")
    commands = {
        "/start": "Welcome message and introduction",
        "/help": "Detailed help and command reference",
        "/search <tags>": "Search for posts with specified tags",
        "/settings": "Open settings menu with inline buttons",
        "/blacklist": "Manage tag blacklist",
        "/blacklist add <tag>": "Add tag to blacklist",
        "/blacklist remove <tag>": "Remove tag from blacklist",
        "/blacklist clear": "Clear entire blacklist",
        "/autotags": "Manage auto-tag toggles",
        "/autotags toggle <tag>": "Enable/disable auto-tag"
    }
    
    for cmd, desc in commands.items():
        print(f"  {cmd:30} - {desc}")
    
    print("\nInline button menus:")
    print("  🚫 Manage Blacklist - View and manage blacklisted tags")
    print("  🏷️ Manage Auto-tags - View and manage auto-tags")
    print("  📊 View Stats - See your settings statistics")
    print("  🔄 Reset Settings - Clear all settings (with confirmation)")


def demo_usage_examples():
    """Show usage examples."""
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)
    
    print("\nExample 1: Basic API search")
    print("```python")
    print("from gelbooru_api import search_posts")
    print("")
    print("posts = search_posts(['cat_ears', 'rating:safe'], limit=10)")
    print("for post in posts:")
    print("    print(f'Post #{post.id}: {post.file_url}')")
    print("```")
    
    print("\nExample 2: Using full client")
    print("```python")
    print("from gelbooru_api import GelbooruClient")
    print("")
    print("with GelbooruClient(api_key='key', user_id='id') as client:")
    print("    posts = client.posts.search(tags=['1girl', 'solo'], limit=20)")
    print("    tags = client.tags.search(name_pattern='cat%')")
    print("```")
    
    print("\nExample 3: Bot usage")
    print("```")
    print("# In Telegram:")
    print("/search cat_ears rating:safe")
    print("/blacklist add glasses")
    print("/autotags toggle rating:safe")
    print("/search cat_ears  # Now automatically excludes glasses and includes rating:safe")
    print("```")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("GELBOORU API WRAPPER & TELEGRAM BOT")
    print("FUNCTIONALITY DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo shows the code structure and functionality")
    print("without requiring actual API credentials.")
    print()
    
    try:
        demo_api_wrapper_structure()
        demo_post_model()
        demo_settings_manager()
        demo_post_filter()
        demo_bot_commands()
        demo_usage_examples()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\n✅ All components demonstrated successfully!")
        print("\nTo use with real data:")
        print("1. Get Telegram bot token from @BotFather")
        print("2. (Optional) Get Gelbooru API credentials")
        print("3. Create .env file with your credentials")
        print("4. Run: python telegram_bot.py")
        print("\nSee README.md for complete documentation.")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()