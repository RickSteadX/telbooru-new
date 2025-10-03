"""
Gelbooru Telegram Bot - Button-Focused Interface
=================================================

A modern Telegram bot for searching Gelbooru with intuitive button navigation.

Features:
- Button-based start menu
- Media album display for search results
- Inline keyboard navigation with pagination
- Post details view
- Tag blacklist management
- Auto-tag toggles
- User settings persistence

Architecture:
- Bot handler manages Telegram interactions
- Settings manager handles user preferences
- Filter system applies blacklists and auto-tags
- Inline keyboards provide intuitive UI
- Pagination system for browsing results

Author: NinjaTech AI
"""

import json
import logging
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict, field
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode

from gelbooru_api import GelbooruClient, Post

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


@dataclass
class SearchSession:
    """Search session data for pagination."""
    user_id: int
    query_tags: List[str]
    posts: List[Post]
    current_page: int = 0
    posts_per_page: int = 10
    
    def get_current_posts(self) -> List[Post]:
        """Get posts for current page."""
        start_idx = self.current_page * self.posts_per_page
        end_idx = start_idx + self.posts_per_page
        return self.posts[start_idx:end_idx]
    
    def has_next_page(self) -> bool:
        """Check if there's a next page."""
        return (self.current_page + 1) * self.posts_per_page < len(self.posts)
    
    def has_prev_page(self) -> bool:
        """Check if there's a previous page."""
        return self.current_page > 0
    
    def get_page_info(self) -> str:
        """Get page information string."""
        total_pages = (len(self.posts) + self.posts_per_page - 1) // self.posts_per_page
        return f"Page {self.current_page + 1}/{total_pages}"


@dataclass
class UserSettings:
    """User settings data structure."""
    user_id: int
    blacklist: List[str] = field(default_factory=list)
    auto_tags: Dict[str, bool] = field(default_factory=dict)
    
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
            User settings
        """
        if user_id not in self.settings:
            self.settings[user_id] = UserSettings(user_id=user_id)
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
        Toggle auto-tag.
        
        Returns:
            New state (True if enabled, False if disabled)
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
    """Utility class for filtering posts."""
    
    @staticmethod
    def apply_blacklist(posts: List[Post], blacklist: List[str]) -> List[Post]:
        """
        Filter posts based on blacklist.
        
        Args:
            posts: List of posts to filter
            blacklist: List of tags to exclude
            
        Returns:
            Filtered posts
        """
        if not blacklist:
            return posts
        
        blacklist_set = set(tag.lower() for tag in blacklist)
        filtered = []
        
        for post in posts:
            post_tags = set(tag.lower() for tag in post.tags)
            if not post_tags.intersection(blacklist_set):
                filtered.append(post)
        
        return filtered
    
    @staticmethod
    def apply_filters(
        posts: List[Post],
        blacklist: List[str],
        max_results: Optional[int] = None
    ) -> List[Post]:
        """
        Apply all filters to posts.
        
        Args:
            posts: List of posts to filter
            blacklist: List of tags to exclude
            max_results: Maximum number of results to return
            
        Returns:
            Filtered posts
        """
        filtered = PostFilter.apply_blacklist(posts, blacklist)
        
        if max_results:
            filtered = filtered[:max_results]
        
        return filtered


class GelbooruBot:
    """
    Main bot class handling Telegram interactions.
    
    Implements button-focused interface with media albums and pagination.
    """
    
    def __init__(
        self,
        telegram_token: str,
        gelbooru_api_key: Optional[str] = None,
        gelbooru_user_id: Optional[str] = None
    ):
        """
        Initialize bot.
        
        Args:
            telegram_token: Telegram bot token
            gelbooru_api_key: Gelbooru API key (optional)
            gelbooru_user_id: Gelbooru user ID (optional)
        """
        self.telegram_token = telegram_token
        self.gelbooru_client = GelbooruClient(
            api_key=gelbooru_api_key,
            user_id=gelbooru_user_id
        )
        self.settings_manager = SettingsManager()
        self.search_sessions: Dict[int, SearchSession] = {}
        
        # Build application
        self.application = Application.builder().token(telegram_token).build()
        self._register_handlers()
    
    def _register_handlers(self):
        """Register command and callback handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        
        # Callback query handler for buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handler for text input
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors in the bot."""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Try to notify the user
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ An error occurred while processing your request. Please try again."
                )
        except:
            pass
    
    def _create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🔍 Search", callback_data="menu_search"),
                InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")
            ],
            [
                InlineKeyboardButton("🚫 Blacklist", callback_data="menu_blacklist"),
                InlineKeyboardButton("🏷️ Auto-tags", callback_data="menu_autotags")
            ],
            [
                InlineKeyboardButton("📊 Statistics", callback_data="menu_stats"),
                InlineKeyboardButton("❓ Help", callback_data="menu_help")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _create_search_results_keyboard(
        self,
        user_id: int,
        show_album_button: bool = True
    ) -> InlineKeyboardMarkup:
        """Create keyboard for search results."""
        session = self.search_sessions.get(user_id)
        if not session:
            return InlineKeyboardMarkup([])
        
        keyboard = []
        
        # Album view button
        if show_album_button:
            keyboard.append([
                InlineKeyboardButton("📸 View as Album", callback_data="search_view_album")
            ])
        
        # Pagination buttons
        nav_buttons = []
        if session.has_prev_page():
            nav_buttons.append(
                InlineKeyboardButton("⬅️ Previous", callback_data="search_prev_page")
            )
        
        nav_buttons.append(
            InlineKeyboardButton(
                f"📄 {session.get_page_info()}",
                callback_data="search_page_info"
            )
        )
        
        if session.has_next_page():
            nav_buttons.append(
                InlineKeyboardButton("➡️ Next", callback_data="search_next_page")
            )
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Back to menu button
        keyboard.append([
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def _create_post_details_keyboard(self, post_index: int, user_id: int) -> InlineKeyboardMarkup:
        """Create keyboard for post details view."""
        session = self.search_sessions.get(user_id)
        if not session:
            return InlineKeyboardMarkup([])
        
        keyboard = [
            [
                InlineKeyboardButton("🔗 Open in Browser", url=f"https://gelbooru.com/index.php?page=post&s=view&id={session.posts[post_index].id}")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Results", callback_data="search_back_to_results")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with button menu."""
        user = update.effective_user
        welcome_text = f"""
👋 **Welcome to Gelbooru Search Bot, {user.first_name}!**

I'm your button-friendly bot for searching Gelbooru with advanced filtering.

🎯 **Quick Features:**
• 📸 View results as media albums
• 🔄 Navigate with pagination buttons
• 🚫 Manage tag blacklist
• 🏷️ Set auto-tags
• ⚙️ Customize your experience

💡 **Get Started:**
Use the buttons below to navigate or type `/search <tags>` to start searching!

Example: `/search cat_ears rating:safe`
"""
        
        keyboard = self._create_main_menu_keyboard()
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu."""
        keyboard = self._create_main_menu_keyboard()
        await update.message.reply_text(
            "🏠 **Main Menu**\n\nChoose an option:",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
📖 **Gelbooru Search Bot Help**

**🔍 Search Commands:**
`/search <tags>` - Search with tags (space-separated)
  Example: `/search cat_ears rating:safe`
  Example: `/search 1girl solo -glasses`

**🎮 Navigation:**
• Use buttons to navigate through menus
• View results as media albums
• Use pagination to browse more results
• Tap on posts to view details

**🏷️ Tag Syntax:**
• Multiple tags: `cat_ears green_eyes`
• Exclude tag: `-glasses`
• Rating filter: `rating:safe`, `rating:questionable`, `rating:explicit`
• Wildcard: `cat*` (matches cat_ears, cat_tail, etc.)
• User filter: `user:username`
• Score filter: `score:>=10`

**🚫 Blacklist:**
Tags in your blacklist are automatically excluded from all searches.
Manage via the Blacklist button in the main menu.

**🏷️ Auto-tags:**
Auto-tags are automatically added to every search.
Example: Enable "rating:safe" to always search safe content.

**⚙️ Settings:**
All preferences are saved automatically and persist between sessions.

Need more help? Visit: https://gelbooru.com/index.php?page=help
"""
        
        keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
        await update.message.reply_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command with media album display."""
        user_id = update.effective_user.id
        
        # Get search tags from command
        if not context.args:
            keyboard = [[InlineKeyboardButton("❓ Help", callback_data="menu_help")]]
            await update.message.reply_text(
                "❌ Please provide search tags.\n"
                "Example: `/search cat_ears rating:safe`",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
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
            posts = self.gelbooru_client.posts.search(tags=all_tags, limit=50)
            
            if not posts:
                keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
                await status_message.edit_text(
                    search_info + "\n\n❌ No results found. Try different tags.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            
            # Apply additional filters
            filtered_posts = PostFilter.apply_filters(
                posts,
                [],  # Blacklist already applied in search
                max_results=50
            )
            
            # Create search session
            session = SearchSession(
                user_id=user_id,
                query_tags=search_tags,
                posts=filtered_posts,
                current_page=0,
                posts_per_page=10
            )
            self.search_sessions[user_id] = session
            
            # Send media album for first page
            await self._send_search_results_album(update, context, user_id, status_message)
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
            await status_message.edit_text(
                search_info + f"\n\n❌ Search failed: {str(e)}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def _send_search_results_album(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        status_message=None
    ):
        """Send search results as media album."""
        session = self.search_sessions.get(user_id)
        if not session:
            return
        
        current_posts = session.get_current_posts()
        
        if not current_posts:
            if status_message:
                await status_message.edit_text("❌ No posts to display.")
            return
        
        # Prepare media group with validation
        media_group = []
        valid_posts = []
        
        for i, post in enumerate(current_posts[:10]):  # Telegram limit: 10 media per group
            # Validate URL
            file_url = post.file_url
            if not file_url or not file_url.startswith(('http://', 'https://')):
                logger.warning(f"Invalid URL for post {post.id}: {file_url}")
                continue
            
            # Skip if URL is too long or contains invalid characters
            if len(file_url) > 2048:
                logger.warning(f"URL too long for post {post.id}")
                continue
            
            caption = None
            if len(media_group) == 0:  # Add caption to first valid media
                caption = (
                    f"📊 **Search Results**\n"
                    f"Found {len(session.posts)} posts\n"
                    f"{session.get_page_info()}\n\n"
                    f"Tap buttons below to navigate"
                )
            
            # Determine media type and add to group
            try:
                if file_url.endswith(('.mp4', '.webm', '.gif')):
                    # For videos, don't use parse_mode in caption to avoid issues
                    media_group.append(InputMediaVideo(media=file_url, caption=caption))
                else:
                    # For photos
                    media_group.append(InputMediaPhoto(media=file_url, caption=caption))
                valid_posts.append(post)
            except Exception as e:
                logger.warning(f"Error preparing media for post {post.id}: {e}")
                continue
        
        # If no valid media, fall back to text
        if not media_group:
            logger.warning("No valid media URLs found, falling back to text")
            await self._send_search_results_text(update, context, user_id, status_message)
            return
        
        # Delete status message if exists
        if status_message:
            try:
                await status_message.delete()
            except:
                pass
        
        # Send media group
        try:
            if update.callback_query:
                chat_id = update.effective_chat.id
                await context.bot.send_media_group(chat_id=chat_id, media=media_group)
            else:
                await update.message.reply_media_group(media=media_group)
            
            # Send keyboard separately
            keyboard = self._create_search_results_keyboard(user_id, show_album_button=False)
            result_text = (
                f"📸 **Showing {len(valid_posts)} of {len(session.posts)} results**\n"
                f"{session.get_page_info()}\n\n"
                f"Use the buttons below to navigate through results."
            )
            
            if update.callback_query:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    result_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error sending media group: {e}")
            # Fallback to text-based results
            await self._send_search_results_text(update, context, user_id, status_message)
    
    async def _send_search_results_text(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        status_message=None
    ):
        """Send search results as text (fallback)."""
        session = self.search_sessions.get(user_id)
        if not session:
            return
        
        current_posts = session.get_current_posts()
        
        result_text = f"📊 **Search Results**\n"
        result_text += f"Found {len(session.posts)} posts\n"
        result_text += f"{session.get_page_info()}\n\n"
        result_text += f"_(Media album unavailable, showing text links)_\n\n"
        
        for i, post in enumerate(current_posts, 1):
            result_text += f"{i}. **Post #{post.id}**\n"
            result_text += f"   Rating: {post.rating}\n"
            result_text += f"   Score: {post.score}\n"
            result_text += f"   🔗 [View]({post.file_url})\n\n"
        
        keyboard = self._create_search_results_keyboard(user_id, show_album_button=True)
        
        # Delete status message if exists
        if status_message:
            try:
                await status_message.delete()
            except:
                pass
        
        try:
            if update.callback_query:
                # Try to edit message, but if it fails, send a new one
                try:
                    await update.callback_query.edit_message_text(
                        result_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    # If edit fails, send new message
                    logger.warning(f"Could not edit message, sending new one: {e}")
                    chat_id = update.effective_chat.id
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_text,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
            else:
                await update.message.reply_text(
                    result_text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
        except Exception as e:
            logger.error(f"Error sending text results: {e}")
            # Last resort - send simple message
            simple_text = f"Found {len(session.posts)} results. Use /search to try again."
            if update.callback_query:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=simple_text
                )
            else:
                await update.message.reply_text(simple_text)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        callback_data = query.data
        
        # Main menu
        if callback_data == "menu_main":
            keyboard = self._create_main_menu_keyboard()
            await query.edit_message_text(
                "🏠 **Main Menu**\n\nChoose an option:",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Search menu
        elif callback_data == "menu_search":
            text = (
                "🔍 **Search**\n\n"
                "To search, use the command:\n"
                "`/search <tags>`\n\n"
                "**Examples:**\n"
                "• `/search cat_ears rating:safe`\n"
                "• `/search 1girl solo -glasses`\n"
                "• `/search landscape rating:safe score:>=10`"
            )
            keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Settings menu
        elif callback_data == "menu_settings":
            settings = self.settings_manager.get_settings(user_id)
            auto_tags = self.settings_manager.get_auto_tags(user_id)
            
            text = "⚙️ **Settings**\n\n"
            text += f"🚫 Blacklisted tags: {len(settings.blacklist)}\n"
            text += f"🏷️ Active auto-tags: {len(auto_tags)}\n\n"
            text += "Use the buttons below to manage your settings."
            
            keyboard = [
                [
                    InlineKeyboardButton("🚫 Blacklist", callback_data="menu_blacklist"),
                    InlineKeyboardButton("🏷️ Auto-tags", callback_data="menu_autotags")
                ],
                [
                    InlineKeyboardButton("🔄 Reset Settings", callback_data="menu_reset")
                ],
                [
                    InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")
                ]
            ]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Blacklist menu
        elif callback_data == "menu_blacklist":
            settings = self.settings_manager.get_settings(user_id)
            text = "🚫 **Blacklist Management**\n\n"
            
            if settings.blacklist:
                text += "**Current blacklist:**\n"
                for tag in settings.blacklist:
                    text += f"• {tag}\n"
                text += "\n"
            else:
                text += "Your blacklist is empty.\n\n"
            
            text += "**To manage blacklist:**\n"
            text += "Send me a message with:\n"
            text += "• `add <tag>` - Add tag to blacklist\n"
            text += "• `remove <tag>` - Remove tag from blacklist\n"
            text += "• `clear` - Clear all blacklisted tags"
            
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu_settings")]]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Auto-tags menu
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
            
            text += "**To manage auto-tags:**\n"
            text += "Send me a message with:\n"
            text += "• `toggle <tag>` - Toggle auto-tag on/off\n\n"
            text += "**Example:**\n"
            text += "`toggle rating:safe`"
            
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu_settings")]]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Statistics menu
        elif callback_data == "menu_stats":
            settings = self.settings_manager.get_settings(user_id)
            auto_tags = self.settings_manager.get_auto_tags(user_id)
            
            text = "📊 **Your Statistics**\n\n"
            text += f"🚫 Blacklisted tags: {len(settings.blacklist)}\n"
            text += f"🏷️ Active auto-tags: {len(auto_tags)}\n"
            text += f"🔧 Total auto-tags: {len(settings.auto_tags)}\n"
            
            if user_id in self.search_sessions:
                session = self.search_sessions[user_id]
                text += f"\n📸 Last search: {len(session.posts)} results\n"
                text += f"📄 Current page: {session.current_page + 1}"
            
            keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # Help menu
        elif callback_data == "menu_help":
            await self.help_command(update, context)
        
        # Reset settings
        elif callback_data == "menu_reset":
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Reset", callback_data="confirm_reset"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_reset")
                ]
            ]
            await query.edit_message_text(
                "⚠️ **Reset Settings**\n\n"
                "This will clear all your settings:\n"
                "• Blacklist\n"
                "• Auto-tags\n\n"
                "Are you sure?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif callback_data == "confirm_reset":
            self.settings_manager.settings[user_id] = UserSettings(user_id=user_id)
            self.settings_manager._save_settings()
            
            keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
            await query.edit_message_text(
                "✅ Settings reset successfully!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif callback_data == "cancel_reset":
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu_settings")]]
            await query.edit_message_text(
                "❌ Reset cancelled.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        # Search pagination
        elif callback_data == "search_prev_page":
            session = self.search_sessions.get(user_id)
            if session and session.has_prev_page():
                session.current_page -= 1
                await self._send_search_results_album(update, context, user_id)
        
        elif callback_data == "search_next_page":
            session = self.search_sessions.get(user_id)
            if session and session.has_next_page():
                session.current_page += 1
                await self._send_search_results_album(update, context, user_id)
        
        elif callback_data == "search_page_info":
            session = self.search_sessions.get(user_id)
            if session:
                await query.answer(
                    f"Showing page {session.current_page + 1} of "
                    f"{(len(session.posts) + session.posts_per_page - 1) // session.posts_per_page}",
                    show_alert=True
                )
        
        elif callback_data == "search_view_album":
            await self._send_search_results_album(update, context, user_id)
        
        elif callback_data == "search_back_to_results":
            await self._send_search_results_text(update, context, user_id)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for blacklist and auto-tag management."""
        user_id = update.effective_user.id
        text = update.message.text.strip().lower()
        
        # Parse command
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return
        
        command, arg = parts
        
        # Blacklist commands
        if command == "add":
            self.settings_manager.add_to_blacklist(user_id, arg)
            await update.message.reply_text(f"✅ Added `{arg}` to blacklist", parse_mode=ParseMode.MARKDOWN)
        
        elif command == "remove":
            self.settings_manager.remove_from_blacklist(user_id, arg)
            await update.message.reply_text(f"✅ Removed `{arg}` from blacklist", parse_mode=ParseMode.MARKDOWN)
        
        elif command == "clear" and arg == "blacklist":
            self.settings_manager.update_blacklist(user_id, [])
            await update.message.reply_text("✅ Blacklist cleared")
        
        # Auto-tag commands
        elif command == "toggle":
            new_state = self.settings_manager.toggle_auto_tag(user_id, arg)
            status = "enabled" if new_state else "disabled"
            await update.message.reply_text(f"✅ Auto-tag `{arg}` {status}", parse_mode=ParseMode.MARKDOWN)
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Gelbooru Bot...")
        self.application.run_polling()
    
    def stop(self):
        """Stop the bot."""
        logger.info("Stopping Gelbooru Bot...")
        self.application.stop()


def main():
    """Main entry point."""
    import os
    
    # Get credentials from environment
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    gelbooru_api_key = os.environ.get("GELBOORU_API_KEY")
    gelbooru_user_id = os.environ.get("GELBOORU_USER_ID")
    
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
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
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        bot.stop()


if __name__ == "__main__":
    main()