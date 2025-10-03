"""
Example Usage Scripts
=====================

Demonstrates how to use the Gelbooru API wrapper and various features.

Author: NinjaTech AI
"""

from gelbooru_api import (
    GelbooruClient,
    search_posts,
    Rating,
    SortField,
    SortOrder
)


def example_1_basic_search():
    """Example 1: Basic post search without authentication."""
    print("=" * 60)
    print("Example 1: Basic Search")
    print("=" * 60)
    
    # Quick search without creating a client
    posts = search_posts(['cat_ears', 'rating:safe'], limit=5)
    
    print(f"\nFound {len(posts)} posts:")
    for i, post in enumerate(posts, 1):
        print(f"\n{i}. Post #{post.id}")
        print(f"   Rating: {post.rating}")
        print(f"   Score: {post.score}")
        print(f"   Tags: {', '.join(post.tag_list[:5])}...")
        print(f"   URL: {post.file_url}")


def example_2_authenticated_search():
    """Example 2: Search with authentication (no rate limits)."""
    print("\n" + "=" * 60)
    print("Example 2: Authenticated Search")
    print("=" * 60)
    
    # Create client with authentication
    # Replace with your actual API key and user ID
    client = GelbooruClient(
        api_key='your_api_key_here',
        user_id='your_user_id_here'
    )
    
    try:
        # Search with multiple tags
        posts = client.posts.search(
            tags=['1girl', 'solo', 'rating:safe'],
            limit=10
        )
        
        print(f"\nFound {len(posts)} posts")
        
        # Filter posts by score
        high_score_posts = [p for p in posts if p.score >= 10]
        print(f"Posts with score >= 10: {len(high_score_posts)}")
        
    finally:
        client.close()


def example_3_advanced_filtering():
    """Example 3: Advanced filtering and tag operations."""
    print("\n" + "=" * 60)
    print("Example 3: Advanced Filtering")
    print("=" * 60)
    
    with GelbooruClient() as client:
        # Search with complex tag query
        posts = client.posts.search(
            tags=[
                'cat_ears',
                'green_eyes',
                '-glasses',  # Exclude glasses
                'rating:safe',
                'score:>=5'
            ],
            limit=20
        )
        
        print(f"\nFound {len(posts)} posts matching criteria")
        
        # Custom filtering
        blacklist = ['school_uniform', 'hat']
        filtered_posts = []
        
        for post in posts:
            if not post.has_any_tag(blacklist):
                filtered_posts.append(post)
        
        print(f"After blacklist filter: {len(filtered_posts)} posts")
        
        # Group by rating
        by_rating = {}
        for post in filtered_posts:
            rating = post.rating
            if rating not in by_rating:
                by_rating[rating] = []
            by_rating[rating].append(post)
        
        print("\nPosts by rating:")
        for rating, posts_list in by_rating.items():
            print(f"  {rating}: {len(posts_list)} posts")


def example_4_tag_search():
    """Example 4: Searching and exploring tags."""
    print("\n" + "=" * 60)
    print("Example 4: Tag Search")
    print("=" * 60)
    
    with GelbooruClient() as client:
        # Search for tags with wildcard
        tags = client.tags.search(
            name_pattern='cat%',
            limit=20
        )
        
        print(f"\nFound {len(tags)} tags starting with 'cat':")
        for tag in tags[:10]:
            print(f"  {tag.name}: {tag.count} posts")
        
        # Get specific tag info
        tag = client.tags.get_by_name('cat_ears')
        if tag:
            print(f"\nTag 'cat_ears' info:")
            print(f"  ID: {tag.id}")
            print(f"  Post count: {tag.count}")
            print(f"  Type: {tag.type}")


def example_5_user_search():
    """Example 5: Searching for users."""
    print("\n" + "=" * 60)
    print("Example 5: User Search")
    print("=" * 60)
    
    with GelbooruClient() as client:
        # Search for users with wildcard
        users = client.users.search(
            name_pattern='admin%',
            limit=10
        )
        
        print(f"\nFound {len(users)} users:")
        for user in users:
            print(f"  {user.name} (ID: {user.id})")


def example_6_post_details():
    """Example 6: Getting detailed post information."""
    print("\n" + "=" * 60)
    print("Example 6: Post Details")
    print("=" * 60)
    
    with GelbooruClient() as client:
        # Get a specific post by ID
        post = client.posts.get_by_id(1)
        
        if post:
            print(f"\nPost #{post.id} details:")
            print(f"  Created: {post.created_at}")
            print(f"  Score: {post.score}")
            print(f"  Dimensions: {post.width}x{post.height}")
            print(f"  Rating: {post.rating}")
            print(f"  Source: {post.source}")
            print(f"  Owner: {post.owner}")
            print(f"  Tags ({len(post.tag_list)}):")
            for tag in post.tag_list[:10]:
                print(f"    - {tag}")
            if len(post.tag_list) > 10:
                print(f"    ... and {len(post.tag_list) - 10} more")


def example_7_batch_processing():
    """Example 7: Batch processing multiple searches."""
    print("\n" + "=" * 60)
    print("Example 7: Batch Processing")
    print("=" * 60)
    
    search_queries = [
        ['cat_ears', 'rating:safe'],
        ['dog_ears', 'rating:safe'],
        ['fox_ears', 'rating:safe']
    ]
    
    with GelbooruClient() as client:
        results = {}
        
        for tags in search_queries:
            posts = client.posts.search(tags=tags, limit=10)
            query_name = ' '.join(tags)
            results[query_name] = len(posts)
        
        print("\nBatch search results:")
        for query, count in results.items():
            print(f"  '{query}': {count} posts")


def example_8_error_handling():
    """Example 8: Proper error handling."""
    print("\n" + "=" * 60)
    print("Example 8: Error Handling")
    print("=" * 60)
    
    from gelbooru_api import GelbooruAPIError, RateLimitError
    
    with GelbooruClient() as client:
        try:
            # This might fail if rate limited
            posts = client.posts.search(tags=['test'], limit=100)
            print(f"Successfully retrieved {len(posts)} posts")
            
        except RateLimitError as e:
            print(f"Rate limit error: {e}")
            print("Consider using API authentication to avoid rate limits")
            
        except GelbooruAPIError as e:
            print(f"API error: {e}")
            
        except Exception as e:
            print(f"Unexpected error: {e}")


def example_9_context_manager():
    """Example 9: Using context manager for automatic cleanup."""
    print("\n" + "=" * 60)
    print("Example 9: Context Manager")
    print("=" * 60)
    
    # The 'with' statement ensures proper cleanup
    with GelbooruClient() as client:
        posts = client.posts.search(tags=['rating:safe'], limit=5)
        print(f"Found {len(posts)} posts")
        
        # Client is automatically closed when exiting the 'with' block
    
    print("Client automatically closed")


def example_10_custom_filtering():
    """Example 10: Custom post filtering logic."""
    print("\n" + "=" * 60)
    print("Example 10: Custom Filtering")
    print("=" * 60)
    
    with GelbooruClient() as client:
        # Get a larger set of posts
        posts = client.posts.search(tags=['rating:safe'], limit=50)
        
        # Custom filter: High score and specific dimensions
        filtered = [
            p for p in posts
            if p.score >= 10 and p.width >= 1920 and p.height >= 1080
        ]
        
        print(f"\nTotal posts: {len(posts)}")
        print(f"High quality posts (score>=10, 1920x1080+): {len(filtered)}")
        
        if filtered:
            print("\nTop 3 high quality posts:")
            for i, post in enumerate(sorted(filtered, key=lambda p: p.score, reverse=True)[:3], 1):
                print(f"{i}. Post #{post.id}")
                print(f"   Score: {post.score}")
                print(f"   Dimensions: {post.width}x{post.height}")
                print(f"   URL: {post.file_url}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("GELBOORU API WRAPPER - EXAMPLE USAGE")
    print("=" * 60)
    
    examples = [
        example_1_basic_search,
        example_2_authenticated_search,
        example_3_advanced_filtering,
        example_4_tag_search,
        example_5_user_search,
        example_6_post_details,
        example_7_batch_processing,
        example_8_error_handling,
        example_9_context_manager,
        example_10_custom_filtering
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nExample failed: {e}")
        
        input("\nPress Enter to continue to next example...")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()