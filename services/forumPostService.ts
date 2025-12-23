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

export const forumPostService = {
  async fetchForumPosts(): Promise<ForumPost[]> {
    try {
      const response = await fetch(getApiUrl());
      if (!response.ok) {
        throw new Error(`Failed to fetch forum posts: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching forum posts:', error);
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

