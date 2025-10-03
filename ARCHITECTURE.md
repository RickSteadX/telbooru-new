# Architecture Documentation

Comprehensive architecture documentation for the Gelbooru API Wrapper and Telegram Bot.

## 🏗️ System Overview

The system consists of two main components:

1. **Gelbooru API Wrapper** - A modular Python library for interacting with the Gelbooru API
2. **Telegram Bot** - A user-friendly interface with inline menus and settings management

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Telegram Bot (telegram_bot.py)             │  │
│  │  • Command Handlers                                   │  │
│  │  • Inline Keyboard Menus                             │  │
│  │  • Callback Handlers                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Business Logic Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Settings Manager                         │  │
│  │  • User Preferences                                   │  │
│  │  • Blacklist Management                              │  │
│  │  • Auto-tag Toggles                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Post Filter                              │  │
│  │  • Blacklist Filtering                               │  │
│  │  • Result Limiting                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Wrapper Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         GelbooruClient (gelbooru_api.py)             │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │           BaseClient                            │ │  │
│  │  │  • HTTP Request Handling                        │ │  │
│  │  │  • Authentication                               │ │  │
│  │  │  • Rate Limiting                                │ │  │
│  │  │  • Error Handling                               │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │         Endpoint Handlers                       │ │  │
│  │  │  • PostsEndpoint                                │ │  │
│  │  │  • TagsEndpoint                                 │ │  │
│  │  │  • UsersEndpoint                                │ │  │
│  │  │  • CommentsEndpoint                             │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Data Model Layer                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Classes                             │  │
│  │  • Post                                               │  │
│  │  • Tag                                                │  │
│  │  • User                                               │  │
│  │  • UserSettings                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│  ┌──────────────────┐         ┌──────────────────────┐     │
│  │  Gelbooru API    │         │   Telegram API       │     │
│  │  (gelbooru.com)  │         │   (telegram.org)     │     │
│  └──────────────────┘         └──────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Component Details

### 1. API Wrapper (gelbooru_api.py)

#### 1.1 BaseClient

**Responsibilities:**
- HTTP request management
- Authentication handling
- Rate limiting and retry logic
- Error handling and exceptions

**Key Methods:**
```python
_build_params(**kwargs) -> Dict[str, Any]
    # Builds request parameters with authentication

_make_request(params, retries=0) -> Union[Dict, List]
    # Makes HTTP request with retry logic
```

**Design Patterns:**
- **Singleton Session**: Reuses HTTP session for efficiency
- **Retry Pattern**: Automatic retry on transient failures
- **Builder Pattern**: Constructs request parameters incrementally

#### 1.2 Endpoint Handlers

**PostsEndpoint:**
```python
search(tags, limit, page, post_id, change_id) -> List[Post]
get_by_id(post_id) -> Optional[Post]
get_deleted(last_id) -> List[Dict]
```

**TagsEndpoint:**
```python
search(name, names, name_pattern, tag_id, after_id, limit, order, order_by) -> List[Tag]
get_by_name(name) -> Optional[Tag]
```

**UsersEndpoint:**
```python
search(name, name_pattern, limit, page) -> List[User]
```

**CommentsEndpoint:**
```python
get_by_post_id(post_id) -> List[Dict]
```

**Design Patterns:**
- **Facade Pattern**: Simplifies complex API interactions
- **Factory Pattern**: Creates data objects from API responses
- **Strategy Pattern**: Different search strategies per endpoint

#### 1.3 Data Models

**Post:**
- Represents a Gelbooru post with all metadata
- Provides helper methods for tag operations
- Immutable dataclass for thread safety

**Tag:**
- Represents tag metadata
- Includes usage statistics

**User:**
- Represents user information
- Minimal data structure

**Design Patterns:**
- **Data Transfer Object (DTO)**: Encapsulates API response data
- **Value Object**: Immutable data structures

### 2. Telegram Bot (telegram_bot.py)

#### 2.1 GelbooruBot

**Responsibilities:**
- Command handling
- User interaction management
- Integration with API wrapper
- Callback query processing

**Command Handlers:**
```python
start_command()      # Welcome message
help_command()       # Help information
search_command()     # Search functionality
settings_command()   # Settings menu
blacklist_command()  # Blacklist management
autotags_command()   # Auto-tag management
```

**Callback Handlers:**
```python
button_callback()    # Inline button interactions
handle_message()     # Text message processing
```

**Design Patterns:**
- **Command Pattern**: Each command is a separate handler
- **Observer Pattern**: Reacts to user interactions
- **Mediator Pattern**: Coordinates between components

#### 2.2 SettingsManager

**Responsibilities:**
- User settings persistence
- Settings CRUD operations
- JSON serialization/deserialization

**Key Methods:**
```python
get_settings(user_id) -> UserSettings
update_blacklist(user_id, blacklist)
add_to_blacklist(user_id, tag)
remove_from_blacklist(user_id, tag)
toggle_auto_tag(user_id, tag) -> bool
get_auto_tags(user_id) -> List[str]
```

**Storage Format:**
```json
{
  "user_id": {
    "user_id": 123456789,
    "blacklist": ["tag1", "tag2"],
    "auto_tags": {
      "rating:safe": true,
      "1girl": false
    }
  }
}
```

**Design Patterns:**
- **Repository Pattern**: Abstracts data storage
- **Singleton Pattern**: Single settings manager instance
- **Lazy Loading**: Loads settings on first access

#### 2.3 PostFilter

**Responsibilities:**
- Apply blacklist filtering
- Limit result count
- Custom filtering logic

**Key Methods:**
```python
apply_blacklist(posts, blacklist) -> List[Post]
apply_filters(posts, blacklist, max_results) -> List[Post]
```

**Design Patterns:**
- **Filter Pattern**: Applies filtering criteria
- **Chain of Responsibility**: Multiple filters can be chained

### 3. Data Flow

#### Search Request Flow

```
User sends /search command
         ↓
Command handler receives request
         ↓
Get user settings (blacklist, auto-tags)
         ↓
Build search query with filters
         ↓
Call GelbooruClient.posts.search()
         ↓
BaseClient makes HTTP request
         ↓
Parse API response into Post objects
         ↓
Apply additional filters
         ↓
Format results for display
         ↓
Send response to user
```

#### Settings Update Flow

```
User clicks inline button
         ↓
Callback handler receives query
         ↓
Parse callback data
         ↓
Update settings via SettingsManager
         ↓
Save settings to JSON file
         ↓
Update inline keyboard
         ↓
Send confirmation to user
```

## 🔧 Design Principles

### 1. Separation of Concerns

Each component has a single, well-defined responsibility:
- **API Wrapper**: External API communication
- **Bot**: User interface and interaction
- **Settings Manager**: Data persistence
- **Post Filter**: Business logic

### 2. Modularity

Components are loosely coupled and can be:
- Tested independently
- Modified without affecting others
- Reused in different contexts
- Extended with new features

### 3. Extensibility

Easy to add new features:
- New API endpoints: Add new endpoint class
- New bot commands: Add new command handler
- New filters: Extend PostFilter class
- New settings: Update UserSettings dataclass

### 4. Error Handling

Comprehensive error handling at each layer:
- **API Layer**: HTTP errors, rate limits, timeouts
- **Bot Layer**: Invalid commands, user errors
- **Settings Layer**: File I/O errors, JSON parsing

### 5. Type Safety

Strong typing throughout:
- Dataclasses for structured data
- Type hints for all functions
- Enums for constants
- Optional types for nullable values

## 🔐 Security Architecture

### 1. Credential Management

```
Environment Variables (.env)
         ↓
Loaded at runtime
         ↓
Never logged or exposed
         ↓
Used only for authentication
```

### 2. Input Validation

All user inputs are validated:
- Command arguments checked
- Tag names sanitized
- Callback data verified
- File paths validated

### 3. Rate Limiting

Multiple layers of protection:
- API wrapper retry logic
- Exponential backoff
- Authentication for unlimited access
- Error handling for rate limit errors

## 📊 Performance Considerations

### 1. HTTP Session Reuse

```python
self.session = requests.Session()
```
- Reuses TCP connections
- Reduces latency
- Improves throughput

### 2. Lazy Loading

Settings loaded only when needed:
```python
if user_id not in self.settings:
    self.settings[user_id] = UserSettings(...)
```

### 3. Efficient Filtering

Filter early to reduce processing:
```python
# Apply blacklist in API query
for bl_tag in blacklist:
    all_tags.append(f"-{bl_tag}")
```

### 4. Context Managers

Automatic resource cleanup:
```python
with GelbooruClient() as client:
    # Resources automatically cleaned up
```

## 🧪 Testing Strategy

### 1. Unit Tests

Test individual components:
- API wrapper methods
- Settings manager operations
- Filter logic
- Data model methods

### 2. Integration Tests

Test component interactions:
- API wrapper + Gelbooru API
- Bot + Settings Manager
- Bot + API Wrapper

### 3. End-to-End Tests

Test complete workflows:
- User search flow
- Settings update flow
- Error handling flow

## 🔄 Future Enhancements

### 1. Async Support

```python
class AsyncGelbooruClient:
    async def search(self, tags):
        async with aiohttp.ClientSession() as session:
            # Async HTTP requests
```

### 2. Caching Layer

```python
class CachedClient:
    def __init__(self, client, cache_ttl=300):
        self.client = client
        self.cache = {}
        self.cache_ttl = cache_ttl
```

### 3. Analytics

```python
class AnalyticsManager:
    def track_search(self, user_id, tags):
        # Track search patterns
    
    def get_popular_tags(self):
        # Analyze usage statistics
```

### 4. Advanced Filtering

```python
class AdvancedFilter:
    def filter_by_score_range(self, posts, min_score, max_score):
        # Score range filtering
    
    def filter_by_dimensions(self, posts, min_width, min_height):
        # Dimension filtering
```

## 📝 Code Quality

### 1. Documentation

- Comprehensive docstrings
- Type hints
- Usage examples
- Architecture documentation

### 2. Code Style

- PEP 8 compliance
- Consistent naming conventions
- Clear variable names
- Logical code organization

### 3. Error Messages

- Clear and actionable
- Include context
- Suggest solutions
- Log appropriately

## 🎯 Design Goals Achieved

✅ **Modularity**: Components are independent and reusable
✅ **Extensibility**: Easy to add new features
✅ **Readability**: Clear code structure and documentation
✅ **Maintainability**: Well-organized and documented
✅ **Scalability**: Can handle growth in users and features
✅ **Reliability**: Comprehensive error handling
✅ **Performance**: Efficient resource usage
✅ **Security**: Proper credential management

---

**Architecture designed by NinjaTech AI**