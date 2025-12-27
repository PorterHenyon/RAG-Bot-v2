// Service for managing forum posts with Discord integration
import type { ForumPost } from '../types';

const getApiUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.length > 0) {
    return `${envUrl}/api/forum-posts`;
  }
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/forum-posts`;
  }
  return '/api/forum-posts';
};

// Cache ETag to enable conditional requests
let cachedPostsEtag: string | null = null;
let cachedPosts: ForumPost[] | null = null;

export const forumPostService = {
  async fetchForumPosts(): Promise<ForumPost[]> {
    try {
      const headers: HeadersInit = {};
      
      // Add conditional request header if we have cached ETag
      if (cachedPostsEtag) {
        headers['If-None-Match'] = cachedPostsEtag;
      }
      
      const response = await fetch(getApiUrl(), { headers });
      
      // If data hasn't changed (304 Not Modified), return cached data
      if (response.status === 304) {
        console.log('✓ Forum posts unchanged, using cache (saved bandwidth)');
        return cachedPosts || [];
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch forum posts: ${response.statusText}`);
      }
      
      // Store ETag for next request
      const etag = response.headers.get('ETag');
      if (etag) {
        cachedPostsEtag = etag;
      }
      
      const posts = await response.json();
      cachedPosts = posts; // Cache the posts
      
      return posts;
    } catch (error) {
      console.error('Error fetching forum posts:', error);
      // Return cached posts if available on error
      if (cachedPosts) {
        console.log('⚠ Using cached forum posts due to error');
        return cachedPosts;
      }
      throw error;
    }
  },

  async updateForumPost(post: ForumPost): Promise<void> {
    try {
      const response = await fetch(getApiUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'update',
          post: post,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update forum post: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error updating forum post:', error);
      throw error;
    }
  },

  async closeDiscordThread(post: ForumPost): Promise<void> {
    try {
      const response = await fetch(getApiUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'close-thread',
          threadId: post.postId,
          channelId: post.forumChannelId,
        }),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || `Failed to close thread: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error closing Discord thread:', error);
      throw error;
    }
  },

  async deleteForumPost(postId: string): Promise<void> {
    try {
      const response = await fetch(getApiUrl(), {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ postId }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `Failed to delete forum post: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting forum post:', error);
      throw error;
    }
  },

  async purgeForumPosts(keepPostIds: string[] = []): Promise<{ deleted: number; kept: number; failed: number }> {
    try {
      // Use bulk purge action for better performance
      const response = await fetch(getApiUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'purge',
          keepPostIds: keepPostIds,
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `Failed to purge forum posts: ${response.statusText}`);
      }
      
      const result = await response.json();
      return {
        deleted: result.deleted || 0,
        kept: result.kept || 0,
        failed: result.failed || 0,
      };
    } catch (error) {
      console.error('Error purging forum posts:', error);
      throw error;
    }
  },
};

