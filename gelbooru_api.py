"""
Gelbooru API Wrapper
====================

A modular and extensible Python wrapper for the Gelbooru API.
Designed with readability, maintainability, and scalability in mind.

Architecture:
- Base client handles HTTP requests and authentication
- Endpoint classes provide specific API functionality
- Response models ensure type safety and validation
- Error handling provides clear feedback

Author: NinjaTech AI
"""

import requests
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Rating(Enum):
    """Post rating enumeration."""
    EXPLICIT = "explicit"
    QUESTIONABLE = "questionable"
    SENSITIVE = "sensitive"
    GENERAL = "general"


class SortOrder(Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class SortField(Enum):
    """Sort field enumeration."""
    ID = "id"
    SCORE = "score"
    RATING = "rating"
    USER = "user"
    HEIGHT = "height"
    WIDTH = "width"
    SOURCE = "source"
    UPDATED = "updated"
    RANDOM = "random"


@dataclass
class Post:
    """Represents a Gelbooru post."""
    id: int
    tags: str
    created_at: str
    score: int
    width: int
    height: int
    md5: str
    directory: str
    image: str
    rating: str
    source: str
    change: int
    owner: str
    creator_id: int
    parent_id: int
    sample: int
    preview_height: int
    preview_width: int
    file_url: str
    sample_url: str
    sample_height: int
    sample_width: int
    preview_url: str
    
    @property
    def tag_list(self) -> List[str]:
        """Returns tags as a list."""
        return self.tags.strip().split()
    
    def has_tag(self, tag: str) -> bool:
        """Check if post has a specific tag."""
        return tag.lower() in [t.lower() for t in self.tag_list]
    
    def has_any_tag(self, tags: List[str]) -> bool:
        """Check if post has any of the specified tags."""
        post_tags = [t.lower() for t in self.tag_list]
        return any(tag.lower() in post_tags for tag in tags)


@dataclass
class Tag:
    """Represents a Gelbooru tag."""
    id: int
    name: str
    count: int
    type: int
    ambiguous: int


@dataclass
class User:
    """Represents a Gelbooru user."""
    id: int
    name: str


class GelbooruAPIError(Exception):
    """Base exception for Gelbooru API errors."""
    pass


class RateLimitError(GelbooruAPIError):
    """Raised when rate limit is exceeded."""
    pass


class AuthenticationError(GelbooruAPIError):
    """Raised when authentication fails."""
    pass


class BaseClient:
    """
    Base HTTP client for Gelbooru API.
    
    Handles:
    - HTTP requests with retry logic
    - Authentication
    - Rate limiting
    - Error handling
    """
    
    BASE_URL = "https://gelbooru.com/index.php"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the base client.
        
        Args:
            api_key: Your Gelbooru API key (optional)
            user_id: Your Gelbooru user ID (optional)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.user_id = user_id
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GelbooruPythonWrapper/1.0'
        })
    
    def _build_params(self, **kwargs) -> Dict[str, Any]:
        """Build request parameters including authentication."""
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        # Add authentication if available
        if self.api_key and self.user_id:
            params['api_key'] = self.api_key
            params['user_id'] = self.user_id
        
        return params
    
    def _make_request(
        self,
        params: Dict[str, Any],
        retries: int = 0
    ) -> Union[Dict, List]:
        """
        Make HTTP request with retry logic.
        
        Args:
            params: Request parameters
            retries: Current retry count
            
        Returns:
            Parsed JSON response
            
        Raises:
            GelbooruAPIError: On request failure
            RateLimitError: On rate limit exceeded
        """
        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            
            # Check for rate limiting
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please try again later.")
            
            # Check for authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Authentication failed. Check your API key and user ID.")
            
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
                return data
            except ValueError:
                logger.error(f"Failed to parse JSON response: {response.text[:200]}")
                raise GelbooruAPIError("Invalid JSON response from API")
                
        except requests.exceptions.Timeout:
            if retries < self.MAX_RETRIES:
                logger.warning(f"Request timeout, retrying... ({retries + 1}/{self.MAX_RETRIES})")
                time.sleep(self.RETRY_DELAY)
                return self._make_request(params, retries + 1)
            raise GelbooruAPIError("Request timeout after multiple retries")
            
        except requests.exceptions.RequestException as e:
            if retries < self.MAX_RETRIES:
                logger.warning(f"Request failed, retrying... ({retries + 1}/{self.MAX_RETRIES})")
                time.sleep(self.RETRY_DELAY)
                return self._make_request(params, retries + 1)
            raise GelbooruAPIError(f"Request failed: {str(e)}")
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()


class PostsEndpoint:
    """
    Posts endpoint handler.
    
    Provides methods for searching and retrieving posts.
    """
    
    def __init__(self, client: BaseClient):
        """Initialize with a base client."""
        self.client = client
    
    def search(
        self,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        page: int = 0,
        post_id: Optional[int] = None,
        change_id: Optional[int] = None
    ) -> List[Post]:
        """
        Search for posts.
        
        Args:
            tags: List of tags to search for
            limit: Maximum number of posts to retrieve (default: 100)
            page: Page number (default: 0)
            post_id: Specific post ID to retrieve
            change_id: Change ID filter
            
        Returns:
            List of Post objects
            
        Example:
            >>> posts = client.posts.search(tags=['cat_ears', 'rating:safe'], limit=10)
            >>> for post in posts:
            ...     print(f"Post {post.id}: {post.file_url}")
        """
        params = self.client._build_params(
            page='dapi',
            s='post',
            q='index',
            json=1,
            limit=limit,
            pid=page,
            id=post_id,
            cid=change_id
        )
        
        # Add tags if provided
        if tags:
            params['tags'] = ' '.join(tags)
        
        response = self.client._make_request(params)
        
        # Handle response format
        if isinstance(response, dict):
            posts_data = response.get('post', [])
        else:
            posts_data = response
        
        # Parse posts
        posts = []
        for post_data in posts_data:
            try:
                post = Post(
                    id=int(post_data.get('id', 0)),
                    tags=post_data.get('tags', ''),
                    created_at=post_data.get('created_at', ''),
                    score=int(post_data.get('score', 0)),
                    width=int(post_data.get('width', 0)),
                    height=int(post_data.get('height', 0)),
                    md5=post_data.get('md5', ''),
                    directory=post_data.get('directory', ''),
                    image=post_data.get('image', ''),
                    rating=post_data.get('rating', ''),
                    source=post_data.get('source', ''),
                    change=int(post_data.get('change', 0)),
                    owner=post_data.get('owner', ''),
                    creator_id=int(post_data.get('creator_id', 0)),
                    parent_id=int(post_data.get('parent_id', 0)),
                    sample=int(post_data.get('sample', 0)),
                    preview_height=int(post_data.get('preview_height', 0)),
                    preview_width=int(post_data.get('preview_width', 0)),
                    file_url=post_data.get('file_url', ''),
                    sample_url=post_data.get('sample_url', ''),
                    sample_height=int(post_data.get('sample_height', 0)),
                    sample_width=int(post_data.get('sample_width', 0)),
                    preview_url=post_data.get('preview_url', '')
                )
                posts.append(post)
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse post data: {e}")
                continue
        
        return posts
    
    def get_by_id(self, post_id: int) -> Optional[Post]:
        """
        Get a specific post by ID.
        
        Args:
            post_id: The post ID
            
        Returns:
            Post object or None if not found
        """
        posts = self.search(post_id=post_id, limit=1)
        return posts[0] if posts else None
    
    def get_deleted(self, last_id: Optional[int] = None) -> List[Dict]:
        """
        Get deleted posts.
        
        Args:
            last_id: Return posts with ID greater than this value
            
        Returns:
            List of deleted post data
        """
        params = self.client._build_params(
            page='dapi',
            s='post',
            q='index',
            deleted='show',
            json=1
        )
        
        if last_id:
            params['last_id'] = last_id
        
        response = self.client._make_request(params)
        
        if isinstance(response, dict):
            return response.get('post', [])
        return response


class TagsEndpoint:
    """
    Tags endpoint handler.
    
    Provides methods for searching and retrieving tags.
    """
    
    def __init__(self, client: BaseClient):
        """Initialize with a base client."""
        self.client = client
    
    def search(
        self,
        name: Optional[str] = None,
        names: Optional[List[str]] = None,
        name_pattern: Optional[str] = None,
        tag_id: Optional[int] = None,
        after_id: Optional[int] = None,
        limit: int = 100,
        order: Optional[SortOrder] = None,
        order_by: Optional[str] = None
    ) -> List[Tag]:
        """
        Search for tags.
        
        Args:
            name: Exact tag name to search for
            names: List of tag names to search for
            name_pattern: Wildcard pattern (use % for multi-char, _ for single-char)
            tag_id: Specific tag ID
            after_id: Get tags with ID greater than this value
            limit: Maximum number of tags to retrieve
            order: Sort order (ASC or DESC)
            order_by: Field to sort by (date, count, name)
            
        Returns:
            List of Tag objects
            
        Example:
            >>> tags = client.tags.search(name_pattern='cat%', limit=20)
            >>> for tag in tags:
            ...     print(f"{tag.name}: {tag.count} posts")
        """
        params = self.client._build_params(
            page='dapi',
            s='tag',
            q='index',
            json=1,
            name=name,
            id=tag_id,
            after_id=after_id,
            limit=limit,
            name_pattern=name_pattern,
            orderby=order_by
        )
        
        if names:
            params['names'] = ' '.join(names)
        
        if order:
            params['order'] = order.value
        
        response = self.client._make_request(params)
        
        # Handle response format
        if isinstance(response, dict):
            tags_data = response.get('tag', [])
        else:
            tags_data = response
        
        # Parse tags
        tags = []
        for tag_data in tags_data:
            try:
                tag = Tag(
                    id=int(tag_data.get('id', 0)),
                    name=tag_data.get('name', ''),
                    count=int(tag_data.get('count', 0)),
                    type=int(tag_data.get('type', 0)),
                    ambiguous=int(tag_data.get('ambiguous', 0))
                )
                tags.append(tag)
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse tag data: {e}")
                continue
        
        return tags
    
    def get_by_name(self, name: str) -> Optional[Tag]:
        """
        Get a specific tag by name.
        
        Args:
            name: The tag name
            
        Returns:
            Tag object or None if not found
        """
        tags = self.search(name=name, limit=1)
        return tags[0] if tags else None


class UsersEndpoint:
    """
    Users endpoint handler.
    
    Provides methods for searching and retrieving users.
    """
    
    def __init__(self, client: BaseClient):
        """Initialize with a base client."""
        self.client = client
    
    def search(
        self,
        name: Optional[str] = None,
        name_pattern: Optional[str] = None,
        limit: int = 100,
        page: int = 0
    ) -> List[User]:
        """
        Search for users.
        
        Args:
            name: Exact username to search for
            name_pattern: Wildcard pattern for username
            limit: Maximum number of users to retrieve
            page: Page number
            
        Returns:
            List of User objects
        """
        params = self.client._build_params(
            page='dapi',
            s='user',
            q='index',
            json=1,
            name=name,
            name_pattern=name_pattern,
            limit=limit,
            pid=page
        )
        
        response = self.client._make_request(params)
        
        # Handle response format
        if isinstance(response, dict):
            users_data = response.get('user', [])
        else:
            users_data = response
        
        # Parse users
        users = []
        for user_data in users_data:
            try:
                user = User(
                    id=int(user_data.get('id', 0)),
                    name=user_data.get('name', '')
                )
                users.append(user)
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse user data: {e}")
                continue
        
        return users


class CommentsEndpoint:
    """
    Comments endpoint handler.
    
    Provides methods for retrieving comments.
    """
    
    def __init__(self, client: BaseClient):
        """Initialize with a base client."""
        self.client = client
    
    def get_by_post_id(self, post_id: int) -> List[Dict]:
        """
        Get comments for a specific post.
        
        Args:
            post_id: The post ID
            
        Returns:
            List of comment data
        """
        params = self.client._build_params(
            page='dapi',
            s='comment',
            q='index',
            json=1,
            post_id=post_id
        )
        
        response = self.client._make_request(params)
        
        if isinstance(response, dict):
            return response.get('comment', [])
        return response


class GelbooruClient:
    """
    Main Gelbooru API client.
    
    Provides a unified interface to all API endpoints.
    
    Example:
        >>> client = GelbooruClient(api_key='your_key', user_id='your_id')
        >>> 
        >>> # Search for posts
        >>> posts = client.posts.search(tags=['cat_ears', 'rating:safe'], limit=10)
        >>> 
        >>> # Search for tags
        >>> tags = client.tags.search(name_pattern='cat%')
        >>> 
        >>> # Get user info
        >>> users = client.users.search(name='username')
        >>> 
        >>> # Close the client when done
        >>> client.close()
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the Gelbooru client.
        
        Args:
            api_key: Your Gelbooru API key (optional, but recommended)
            user_id: Your Gelbooru user ID (optional, but recommended)
            timeout: Request timeout in seconds
        """
        self._base_client = BaseClient(api_key, user_id, timeout)
        
        # Initialize endpoint handlers
        self.posts = PostsEndpoint(self._base_client)
        self.tags = TagsEndpoint(self._base_client)
        self.users = UsersEndpoint(self._base_client)
        self.comments = CommentsEndpoint(self._base_client)
    
    def close(self):
        """Close the client and cleanup resources."""
        self._base_client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick usage
def search_posts(
    tags: List[str],
    limit: int = 10,
    api_key: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Post]:
    """
    Quick function to search for posts without creating a client.
    
    Args:
        tags: List of tags to search for
        limit: Maximum number of posts
        api_key: Optional API key
        user_id: Optional user ID
        
    Returns:
        List of Post objects
        
    Example:
        >>> posts = search_posts(['cat_ears', 'rating:safe'], limit=5)
    """
    with GelbooruClient(api_key, user_id) as client:
        return client.posts.search(tags=tags, limit=limit)