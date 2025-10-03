"""
Gelbooru Telegram Bot
=====================

A Telegram bot for searching Gelbooru with inline button menus.

Features:
- Tag blacklist management
- Auto-tag toggles
- Inline keyboard navigation
- User settings persistence
- Search with filters

Architecture:
- Bot handler manages Telegram interactions
- Settings manager handles user preferences
- Filter system applies blacklists and auto-tags
- Inline keyboards provide intuitive UI

Author: NinjaTech AI
"""

import json
import logging
from typing import List, Dict, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from gelbooru_api import GelbooruClient, Post

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


@dataclass
class UserSettings:
    """User settings data structure."""
    user_id: int
    blacklist: List[str]
    auto_tags: Dict[str, bool]  # tag -> enabled
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSettings':
        """Create from dictionary."""
        return cls(**data)


class SettingsManager:
    """
    Manages user settings with file-based persistence.
    
    Settings are stored in JSON format for easy editing and portability.
    """
    
    def __init__(self, settings_file: str = "user_settings.json"):
        """
        Initialize settings manager.
        
        Args:
            settings_file: Path to settings file
        """
        self.settings_file = Path(settings_file)
        self.settings: Dict[int, UserSettings] = {}
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.settings = {
                        int(user_id): UserSettings.from_dict(settings)
                        for user_id, settings in data.items()
                    }
                logger.info(f"Loaded settings for {len(self.settings)} users")
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")
                self.settings = {}
        else:
            logger.info("No existing settings file found, starting fresh")
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            data = {
                str(user_id): settings.to_dict()
                for user_id, settings in self.settings.items()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved settings for {len(self.settings)} users")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def get_settings(self, user_id: int) -> UserSettings:
        """
        Get settings for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            UserSettings object
        """
        if user_id not in self.settings:
            self.settings[user_id] = UserSettings(
                user_id=user_id,
                blacklist=[],
                auto_tags={}
            )
            self._save_settings()
        return self.settings[user_id]
    
    def update_blacklist(self, user_id: int, blacklist: List[str]):
        """Update user's blacklist."""
        settings = self.get_settings(user_id)
        settings.blacklist = blacklist
        self._save_settings()
    
    def add_to_blacklist(self, user_id: int, tag: str):
        """Add tag to blacklist."""
        settings = self.get_settings(user_id)
        if tag not in settings.blacklist:
            settings.blacklist.append(tag)
            self._save_settings()
    
    def remove_from_blacklist(self, user_id: int, tag: str):
        """Remove tag from blacklist."""
        settings = self.get_settings(user_id)
        if tag in settings.blacklist:
            settings.blacklist.remove(tag)
            self._save_settings()
    
    def toggle_auto_tag(self, user_id: int, tag: str) -> bool:
        """
        Toggle auto-tag on/off.
        
        Returns:
            New state (True = enabled, False = disabled)
        """
        settings = self.get_settings(user_id)
        current_state = settings.auto_tags.get(tag, False)
        settings.auto_tags[tag] = not current_state
        self._save_settings()
        return settings.auto_tags[tag]
    
    def get_auto_tags(self, user_id: int) -> List[str]:
        """Get list of enabled auto-tags."""
        settings = self.get_settings(user_id)
        return [tag for tag, enabled in settings.auto_tags.items() if enabled]


class PostFilter:
    """
    Filters posts based on user settings.
    
    Applies blacklist and other filtering rules.
    """
    
    @staticmethod
    def apply_blacklist(posts: List[Post], blacklist: List[str]) -> List[Post]:
        """
        Filter out posts containing blacklisted tags.
        
        Args:
            posts: List of posts to filter
            blacklist: List of blacklisted tags
            
        Returns:
            Filtered list of posts
        """
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
    def apply_filters(
        posts: List[Post],
        blacklist: List[str],
        max_results: int = 10
    ) -> List[Post]:
        """
        Apply all filters to posts.
        
        Args:
            posts: List of posts to filter
            blacklist: Blacklisted tags
            max_results: Maximum number of results
            
        Returns:
            Filtered and limited list of posts
        """
        filtered = PostFilter.apply_blacklist(posts, blacklist)
        return filtered[:max_results]


class GelbooruBot:
    """
    Main Telegram bot class.
    
    Handles all bot interactions and commands.
    """
    
    def __init__(
        self,
        telegram_token: str,
        gelbooru_api_key: Optional[str] = None,
        gelbooru_user_id: Optional[str] = None
    ):
        """
        Initialize the bot.
        
        Args:
            telegram_token: Telegram bot token
            gelbooru_api_key: Gelbooru API key (optional)
            gelbooru_user_id: Gelbooru user ID (optional)
        """
        self.telegram_token = telegram_token
        self.gelbooru_api_key = gelbooru_api_key
        self.gelbooru_user_id = gelbooru_user_id
        self.settings_manager = SettingsManager()
        self.gelbooru_client = GelbooruClient(gelbooru_api_key, gelbooru_user_id)
        
        # Build application
        self.application = Application.builder().token(telegram_token).build()
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all command and callback handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("blacklist", self.blacklist_command))
        self.application.add_handler(CommandHandler("autotags", self.autotags_command))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for text input
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        welcome_text = f"""
👋 Welcome to Gelbooru Search Bot, {user.first_name}!

I can help you search Gelbooru with advanced filtering options.

🔍 **Commands:**
/search <tags> - Search for posts
/settings - View and manage your settings
/blacklist - Manage your tag blacklist
/autotags - Manage auto-tag toggles
/help - Show detailed help

💡 **Quick Start:**
Try: /search cat_ears rating:safe

Get started by configuring your settings with /settings
"""
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📖 **Gelbooru Search Bot Help**

**Search Commands:**
/search <tags> - Search with tags (space-separated)
  Example: /search cat_ears rating:safe
  Example: /search 1girl solo -glasses

**Settings Commands:**
/settings - Open settings menu
/blacklist - Manage blacklisted tags
/autotags - Manage auto-tags

**Tag Syntax:**
• Multiple tags: cat_ears green_eyes
• Exclude tag: -glasses
• Rating filter: rating:safe, rating:questionable, rating:explicit
• Wildcard: cat* (matches cat_ears, cat_tail, etc.)
• User filter: user:username
• Score filter: score:>=10

**Blacklist:**
Tags in your blacklist will be automatically excluded from all searches.
Use /blacklist to add or remove tags.

**Auto-tags:**
Auto-tags are automatically added to every search.
Use /autotags to enable/disable specific tags.
Example: Enable "rating:safe" to always search safe content.

**Settings:**
All your preferences are saved automatically and persist between sessions.

Need more help? Visit: https://gelbooru.com/index.php?page=help
"""
        await update.message.reply_text(help_text)
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command."""
        user_id = update.effective_user.id
        
        # Get search tags from command
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide search tags.\n"
                "Example: /search cat_ears rating:safe"
            )
            return
        
        search_tags = context.args
        
        # Get user settings
        settings = self.settings_manager.get_settings(user_id)
        
        # Add auto-tags
        auto_tags = self.settings_manager.get_auto_tags(user_id)
        all_tags = search_tags + auto_tags
        
        # Add blacklist as negative tags
        for bl_tag in settings.blacklist:
            all_tags.append(f"-{bl_tag}")
        
        # Show search info
        search_info = f"🔍 Searching for: {' '.join(search_tags)}"
        if auto_tags:
            search_info += f"\n🏷️ Auto-tags: {' '.join(auto_tags)}"
        if settings.blacklist:
            search_info += f"\n🚫 Blacklist: {' '.join(settings.blacklist)}"
        
        status_message = await update.message.reply_text(search_info + "\n\n⏳ Searching...")
        
        try:
            # Search Gelbooru
            posts = self.gelbooru_client.posts.search(tags=all_tags, limit=20)
            
            if not posts:
                await status_message.edit_text(
                    search_info + "\n\n❌ No results found. Try different tags."
                )
                return
            
            # Apply additional filters
            filtered_posts = PostFilter.apply_filters(
                posts,
                [],  # Blacklist already applied in search
                max_results=10
            )
            
            # Format results
            result_text = search_info + f"\n\n✅ Found {len(filtered_posts)} results:\n\n"
            
            for i, post in enumerate(filtered_posts[:5], 1):
                result_text += f"{i}. Post #{post.id}\n"
                result_text += f"   Rating: {post.rating}\n"
                result_text += f"   Score: {post.score}\n"
                result_text += f"   🔗 {post.file_url}\n\n"
            
            if len(filtered_posts) > 5:
                result_text += f"... and {len(filtered_posts) - 5} more results"
            
            await status_message.edit_text(result_text)
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            await status_message.edit_text(
                search_info + f"\n\n❌ Search failed: {str(e)}"
            )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        user_id = update.effective_user.id
        settings = self.settings_manager.get_settings(user_id)
        
        # Build settings text
        settings_text = "⚙️ **Your Settings**\n\n"
        settings_text += f"🚫 **Blacklist:** {len(settings.blacklist)} tags\n"
        if settings.blacklist:
            settings_text += f"   {', '.join(settings.blacklist[:5])}"
            if len(settings.blacklist) > 5:
                settings_text += f" (+{len(settings.blacklist) - 5} more)"
        settings_text += "\n\n"
        
        auto_tags = self.settings_manager.get_auto_tags(user_id)
        settings_text += f"🏷️ **Auto-tags:** {len(auto_tags)} enabled\n"
        if auto_tags:
            settings_text += f"   {', '.join(auto_tags[:5])}"
            if len(auto_tags) > 5:
                settings_text += f" (+{len(auto_tags) - 5} more)"
        
        # Build inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("🚫 Manage Blacklist", callback_data="menu_blacklist"),
                InlineKeyboardButton("🏷️ Manage Auto-tags", callback_data="menu_autotags")
            ],
            [
                InlineKeyboardButton("📊 View Stats", callback_data="menu_stats"),
                InlineKeyboardButton("🔄 Reset Settings", callback_data="menu_reset")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def blacklist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /blacklist command."""
        user_id = update.effective_user.id
        settings = self.settings_manager.get_settings(user_id)
        
        if not context.args:
            # Show current blacklist
            if settings.blacklist:
                text = "🚫 **Your Blacklist:**\n\n"
                for tag in settings.blacklist:
                    text += f"• {tag}\n"
                text += "\n**Usage:**\n"
                text += "Add: /blacklist add <tag>\n"
                text += "Remove: /blacklist remove <tag>\n"
                text += "Clear: /blacklist clear"
            else:
                text = "🚫 Your blacklist is empty.\n\n"
                text += "**Add tags to blacklist:**\n"
                text += "/blacklist add <tag>"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        action = context.args[0].lower()
        
        if action == "add" and len(context.args) > 1:
            tag = context.args[1]
            self.settings_manager.add_to_blacklist(user_id, tag)
            await update.message.reply_text(f"✅ Added '{tag}' to blacklist")
        
        elif action == "remove" and len(context.args) > 1:
            tag = context.args[1]
            self.settings_manager.remove_from_blacklist(user_id, tag)
            await update.message.reply_text(f"✅ Removed '{tag}' from blacklist")
        
        elif action == "clear":
            self.settings_manager.update_blacklist(user_id, [])
            await update.message.reply_text("✅ Blacklist cleared")
        
        else:
            await update.message.reply_text(
                "❌ Invalid command.\n"
                "Usage: /blacklist [add|remove|clear] <tag>"
            )
    
    async def autotags_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /autotags command."""
        user_id = update.effective_user.id
        settings = self.settings_manager.get_settings(user_id)
        
        if not context.args:
            # Show current auto-tags
            auto_tags = self.settings_manager.get_auto_tags(user_id)
            
            if auto_tags:
                text = "🏷️ **Your Auto-tags:**\n\n"
                for tag in auto_tags:
                    text += f"✅ {tag}\n"
                text += "\n**Disabled Auto-tags:**\n"
                disabled = [t for t, e in settings.auto_tags.items() if not e]
                for tag in disabled:
                    text += f"❌ {tag}\n"
                text += "\n**Usage:**\n"
                text += "Toggle: /autotags toggle <tag>"
            else:
                text = "🏷️ No auto-tags enabled.\n\n"
                text += "**Enable auto-tags:**\n"
                text += "/autotags toggle <tag>\n\n"
                text += "**Example:**\n"
                text += "/autotags toggle rating:safe"
            
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        action = context.args[0].lower()
        
        if action == "toggle" and len(context.args) > 1:
            tag = context.args[1]
            new_state = self.settings_manager.toggle_auto_tag(user_id, tag)
            status = "enabled" if new_state else "disabled"
            emoji = "✅" if new_state else "❌"
            await update.message.reply_text(f"{emoji} Auto-tag '{tag}' {status}")
        
        else:
            await update.message.reply_text(
                "❌ Invalid command.\n"
                "Usage: /autotags toggle <tag>"
            )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        callback_data = query.data
        
        if callback_data == "menu_blacklist":
            settings = self.settings_manager.get_settings(user_id)
            text = "🚫 **Blacklist Management**\n\n"
            
            if settings.blacklist:
                text += "**Current blacklist:**\n"
                for tag in settings.blacklist:
                    text += f"• {tag}\n"
                text += "\n"
            else:
                text += "Your blacklist is empty.\n\n"
            
            text += "**Commands:**\n"
            text += "• /blacklist add <tag>\n"
            text += "• /blacklist remove <tag>\n"
            text += "• /blacklist clear"
            
            await query.edit_message_text(text, parse_mode='Markdown')
        
        elif callback_data == "menu_autotags":
            settings = self.settings_manager.get_settings(user_id)
            auto_tags = self.settings_manager.get_auto_tags(user_id)
            
            text = "🏷️ **Auto-tags Management**\n\n"
            
            if auto_tags:
                text += "**Enabled auto-tags:**\n"
                for tag in auto_tags:
                    text += f"✅ {tag}\n"
                text += "\n"
            else:
                text += "No auto-tags enabled.\n\n"
            
            text += "**Commands:**\n"
            text += "• /autotags toggle <tag>\n\n"
            text += "**Example:**\n"
            text += "/autotags toggle rating:safe"
            
            await query.edit_message_text(text, parse_mode='Markdown')
        
        elif callback_data == "menu_stats":
            settings = self.settings_manager.get_settings(user_id)
            auto_tags = self.settings_manager.get_auto_tags(user_id)
            
            text = "📊 **Your Statistics**\n\n"
            text += f"🚫 Blacklisted tags: {len(settings.blacklist)}\n"
            text += f"🏷️ Active auto-tags: {len(auto_tags)}\n"
            text += f"🔧 Total auto-tags: {len(settings.auto_tags)}\n"
            
            await query.edit_message_text(text, parse_mode='Markdown')
        
        elif callback_data == "menu_reset":
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Reset", callback_data="confirm_reset"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_reset")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "⚠️ **Reset Settings**\n\n"
                "This will clear all your settings:\n"
                "• Blacklist\n"
                "• Auto-tags\n\n"
                "Are you sure?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        elif callback_data == "confirm_reset":
            self.settings_manager.settings[user_id] = UserSettings(
                user_id=user_id,
                blacklist=[],
                auto_tags={}
            )
            self.settings_manager._save_settings()
            
            await query.edit_message_text("✅ Settings reset successfully!")
        
        elif callback_data == "cancel_reset":
            await query.edit_message_text("❌ Reset cancelled.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        # For future expansion - could handle natural language queries
        await update.message.reply_text(
            "💡 Use /search <tags> to search, or /help for more information."
        )
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Gelbooru Telegram Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def stop(self):
        """Stop the bot and cleanup."""
        logger.info("Stopping bot...")
        self.gelbooru_client.close()


def main():
    """Main entry point."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    gelbooru_api_key = os.getenv('GELBOORU_API_KEY')
    gelbooru_user_id = os.getenv('GELBOORU_USER_ID')
    
    if not telegram_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Create and run bot
    bot = GelbooruBot(
        telegram_token=telegram_token,
        gelbooru_api_key=gelbooru_api_key,
        gelbooru_user_id=gelbooru_user_id
    )
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        bot.stop()


if __name__ == '__main__':
    main()