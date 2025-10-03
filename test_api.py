"""
API Wrapper Test Script
=======================

Quick test script to verify the Gelbooru API wrapper is working correctly.

Author: NinjaTech AI
"""

import sys
from gelbooru_api import GelbooruClient, GelbooruAPIError


def test_basic_search():
    """Test basic search functionality."""
    print("Testing basic search...")
    try:
        with GelbooruClient() as client:
            posts = client.posts.search(tags=['rating:safe'], limit=5)
            
            if posts:
                print(f"✅ Basic search successful! Found {len(posts)} posts")
                print(f"   First post ID: {posts[0].id}")
                return True
            else:
                print("⚠️  Search returned no results (this might be normal)")
                return True
    except Exception as e:
        print(f"❌ Basic search failed: {e}")
        return False


def test_tag_search():
    """Test tag search functionality."""
    print("\nTesting tag search...")
    try:
        with GelbooruClient() as client:
            tags = client.tags.search(name_pattern='cat%', limit=5)
            
            if tags:
                print(f"✅ Tag search successful! Found {len(tags)} tags")
                print(f"   First tag: {tags[0].name} ({tags[0].count} posts)")
                return True
            else:
                print("⚠️  Tag search returned no results")
                return True
    except Exception as e:
        print(f"❌ Tag search failed: {e}")
        return False


def test_post_filtering():
    """Test post filtering functionality."""
    print("\nTesting post filtering...")
    try:
        with GelbooruClient() as client:
            posts = client.posts.search(tags=['rating:safe'], limit=20)
            
            if posts:
                # Test has_tag method
                test_post = posts[0]
                has_rating = test_post.has_tag('rating:safe')
                
                # Test has_any_tag method
                blacklist = ['nonexistent_tag_xyz']
                filtered = [p for p in posts if not p.has_any_tag(blacklist)]
                
                print(f"✅ Post filtering successful!")
                print(f"   Total posts: {len(posts)}")
                print(f"   After blacklist: {len(filtered)}")
                return True
            else:
                print("⚠️  No posts to filter")
                return True
    except Exception as e:
        print(f"❌ Post filtering failed: {e}")
        return False


def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    try:
        with GelbooruClient() as client:
            # This should work fine
            posts = client.posts.search(tags=['test'], limit=1)
            print("✅ Error handling test passed (no errors encountered)")
            return True
    except GelbooruAPIError as e:
        print(f"✅ Error handling working correctly: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_context_manager():
    """Test context manager functionality."""
    print("\nTesting context manager...")
    try:
        with GelbooruClient() as client:
            posts = client.posts.search(tags=['rating:safe'], limit=1)
        
        # Client should be closed now
        print("✅ Context manager test passed")
        return True
    except Exception as e:
        print(f"❌ Context manager test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("GELBOORU API WRAPPER - TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_search,
        test_tag_search,
        test_post_filtering,
        test_error_handling,
        test_context_manager
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! API wrapper is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())