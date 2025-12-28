// Vercel API route for managing forum posts from Discord bot
import type { VercelRequest, VercelResponse } from '@vercel/node';

interface ForumPost {
  id: string;
  user: {
    username: string;
    id: string;
    avatarUrl: string;
  };
  postTitle: string;
  status: string;
  tags: string[];
  createdAt: string;
  forumChannelId: string;
  postId: string;
  conversation: Array<{
    author: string;
    content: string;
    timestamp: string;
  }>;
  logs?: string;
}

interface CloseThreadRequest {
  threadId: string;
  channelId: string;
}

// RESOURCE OPTIMIZATION: Forum posts are stored in-memory only (not persisted to Vercel KV to save costs)
// Data resets on restart but saves significant storage and API costs
let inMemoryForumPosts: ForumPost[] = [];

// Helper functions to get/set forum posts
async function getForumPosts(): Promise<ForumPost[]> {
  // RESOURCE OPTIMIZATION: Forum posts are NOT loaded from Vercel KV to save costs
  // Only return in-memory posts - data resets on restart but saves significant Vercel costs
  return inMemoryForumPosts;
}

async function saveForumPosts(posts: ForumPost[]): Promise<void> {
  // RESOURCE OPTIMIZATION: Forum posts are NOT saved to Vercel KV to save storage costs
  // Only use in-memory storage - data resets on restart but saves significant Vercel costs
  // Bot still monitors and responds to forum posts, but doesn't persist them
  inMemoryForumPosts = posts;
  console.log(`💾 Forum posts stored in-memory only (${posts.length} posts) - NOT persisted to Vercel KV to save costs`);
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // Return all forum posts with caching to reduce bandwidth
    try {
      const posts = await getForumPosts();
      
      // Generate ETag from posts hash for conditional requests
      const crypto = await import('crypto');
      const postsString = JSON.stringify(posts);
      const etag = crypto.createHash('md5').update(postsString).digest('hex');
      
      // Check if client has cached version (conditional request)
      const clientEtag = req.headers['if-none-match'];
      if (clientEtag === etag) {
        // Data hasn't changed, return 304 Not Modified (saves bandwidth!)
        res.setHeader('ETag', etag);
        res.setHeader('Cache-Control', 'public, max-age=30, must-revalidate'); // Cache for 30 seconds
        return res.status(304).end();
      }
      
      // Set caching headers
      res.setHeader('ETag', etag);
      res.setHeader('Cache-Control', 'public, max-age=30, must-revalidate'); // Cache for 30 seconds
      res.setHeader('Content-Type', 'application/json');
      
      return res.status(200).json(posts);
    } catch (error) {
      console.error('Error fetching forum posts:', error);
      return res.status(200).json(inMemoryForumPosts);
    }
  }

  if (req.method === 'POST') {
    try {
      // Log request for debugging
      console.log('POST request received to /api/forum-posts');
      console.log('Request body:', JSON.stringify(req.body, null, 2));
      
      const action = req.body?.action;

      if (!action) {
        console.error('No action specified in request body');
        return res.status(400).json({ error: 'Missing action in request body' });
      }

      if (action === 'create') {
        // Bot is creating a new forum post
        const post: ForumPost = req.body.post;
        if (post) {
          const posts = await getForumPosts();
          // Check if post already exists
          const existingIndex = posts.findIndex(p => p.id === post.id);
          if (existingIndex >= 0) {
            posts[existingIndex] = post;
          } else {
            posts.push(post);
          }
          await saveForumPosts(posts);
          return res.status(200).json({ success: true, data: post });
        }
      }

      if (action === 'update') {
        // Update an existing forum post
        const post: ForumPost = req.body.post;
        const posts = await getForumPosts();
        const index = posts.findIndex(p => p.id === post.id || p.postId === post.postId);
        
        if (index >= 0) {
          // Merge existing post with updates (preserve fields that weren't updated)
          posts[index] = { ...posts[index], ...post };
          await saveForumPosts(posts);
          return res.status(200).json({ success: true, data: posts[index] });
        }
        
        // If post not found, create it (bot might have missed initial create)
        if (post.id && post.postId) {
          posts.push(post);
          await saveForumPosts(posts);
          return res.status(200).json({ success: true, data: post, message: 'Post created (was not found)' });
        }
        
        return res.status(404).json({ error: 'Post not found' });
      }

      if (action === 'close-thread') {
        // Close a Discord thread
        const { threadId }: CloseThreadRequest = req.body;
        const DISCORD_BOT_TOKEN = process.env.DISCORD_BOT_TOKEN;
        
        if (!DISCORD_BOT_TOKEN) {
          return res.status(500).json({ error: 'Discord bot token not configured' });
        }

        try {
          // Use Discord API to archive/close the thread
          const discordResponse = await fetch(
            `https://discord.com/api/v10/channels/${threadId}`,
            {
              method: 'PATCH',
              headers: {
                'Authorization': `Bot ${DISCORD_BOT_TOKEN}`,
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                archived: true,
                locked: true,
              }),
            }
          );

          if (!discordResponse.ok) {
            const error = await discordResponse.text();
            return res.status(discordResponse.status).json({ error: `Discord API error: ${error}` });
          }

          // Update the post status in our storage
          const posts = await getForumPosts();
          const postIndex = posts.findIndex(p => p.postId === threadId || p.id === threadId);
          if (postIndex >= 0) {
            posts[postIndex].status = 'Closed';
            await saveForumPosts(posts);
          }

          return res.status(200).json({ success: true, message: 'Thread closed in Discord' });
        } catch (error: any) {
          return res.status(500).json({ error: `Failed to close thread: ${error.message}` });
        }
      }

      if (action === 'delete') {
        // Delete a forum post from the dashboard
        const postId = req.body.postId;
        if (postId) {
          const posts = await getForumPosts();
          const filteredPosts = posts.filter(p => p.id !== postId && p.postId !== postId.replace('POST-', ''));
          await saveForumPosts(filteredPosts);
          console.log(`Deleted post ${postId} from dashboard`);
          return res.status(200).json({ success: true, message: 'Post deleted' });
        }
        return res.status(400).json({ error: 'Missing postId' });
      }

      if (action === 'cleanup') {
        // Clean up old forum posts by retention days
        const retentionDays = req.body.retentionDays || 7;
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);
        
        try {
          const posts = await getForumPosts();
          const initialLength = posts.length;
          
          // Filter out old solved/closed posts
          const filteredPosts = posts.filter((post: any) => {
            if (post.status === 'Solved' || post.status === 'Closed') {
              const postDate = new Date(post.createdAt || post.updatedAt);
              return postDate > cutoffDate;
            }
            return true; // Keep unsolved posts
          });
          
          await saveForumPosts(filteredPosts);
          
          const deleted = initialLength - filteredPosts.length;
          console.log(`Cleaned up ${deleted} old forum posts (kept posts newer than ${retentionDays} days)`);
          
          return res.status(200).json({
            success: true,
            deleted,
            kept: filteredPosts.length,
            message: `Cleaned up ${deleted} old forum posts (kept posts newer than ${retentionDays} days)`
          });
        } catch (error: any) {
          console.error('Error cleaning up forum posts:', error);
          return res.status(500).json({ error: `Failed to cleanup posts: ${error.message}` });
        }
      }

      if (action === 'purge') {
        // Bulk purge forum posts (delete all except kept ones)
        const keepPostIds: string[] = req.body.keepPostIds || [];
        try {
          const posts = await getForumPosts();
          const initialLength = posts.length;
          
          // Filter posts to keep
          const postsToKeep = posts.filter(post => {
            const postId = post.id || post.postId;
            const postIdWithoutPrefix = postId.replace('POST-', '');
            
            // Check if this post should be kept
            return keepPostIds.some(keepId => {
              const keepIdWithoutPrefix = keepId.replace('POST-', '');
              return (
                postId === keepId ||
                postIdWithoutPrefix === keepId ||
                postId === `POST-${keepId}` ||
                postIdWithoutPrefix === keepIdWithoutPrefix ||
                post.postId === keepId ||
                post.postId === keepIdWithoutPrefix
              );
            });
          });
          
          // Save only the posts to keep
          await saveForumPosts(postsToKeep);
          
          const deleted = initialLength - postsToKeep.length;
          console.log(`Purged ${deleted} forum posts (kept ${postsToKeep.length})`);
          
          return res.status(200).json({
            success: true,
            deleted,
            kept: postsToKeep.length,
            failed: 0,
            message: `Purged ${deleted} posts, kept ${postsToKeep.length}`
          });
        } catch (error: any) {
          console.error('Error purging forum posts:', error);
          return res.status(500).json({ error: `Failed to purge posts: ${error.message}` });
        }
      }

      return res.status(400).json({ error: 'Invalid action' });
    } catch (error) {
      return res.status(400).json({ error: 'Invalid request body' });
    }
  }

  if (req.method === 'DELETE') {
    // Delete a forum post (support both body and query parameter)
    try {
      // Try to get postId from body first, then query
      const postId = req.body?.postId || req.query?.postId;
      if (postId) {
        const posts = await getForumPosts();
        const initialLength = posts.length;
        // Check both id and postId fields (same as POST action='delete')
        const filtered = posts.filter(p => p.id !== postId && p.postId !== postId.replace('POST-', ''));
        await saveForumPosts(filtered);
        const deleted = initialLength > filtered.length;
        if (deleted) {
          console.log(`Deleted post ${postId} from dashboard via DELETE method`);
          return res.status(200).json({ success: true, message: 'Post deleted' });
        }
        // Even if not found in API, return success (might be local mock data)
        return res.status(200).json({ success: true, message: 'Post deleted (was not in API)' });
      }
      return res.status(400).json({ error: 'Post ID required' });
    } catch (error) {
      console.error('Error in DELETE handler:', error);
      return res.status(400).json({ error: 'Invalid request' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}

