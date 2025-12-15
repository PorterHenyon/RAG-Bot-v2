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

// Persistent storage using Vercel KV (Redis)
// Falls back to in-memory if KV not configured
let kvClient: any = null;
let inMemoryForumPosts: ForumPost[] = [];

// Initialize KV/Redis client if available (lazy import)
async function initKV() {
  if (kvClient) return; // Already initialized
  
  // Try Vercel KV first (REST API)
  if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
    try {
      const kvModule = await import('@vercel/kv');
      kvClient = kvModule.kv;
      console.log('✓ Using Vercel KV for forum posts (persistent storage)');
      return;
    } catch (e) {
      console.log('⚠ Vercel KV not available, trying direct Redis connection...');
    }
  }
  
  // Try direct Redis connection (Redis Cloud, etc.)
  // Check both REDIS_URL and STORAGE_URL (Vercel custom prefix)
  const redisUrl = process.env.REDIS_URL || process.env.STORAGE_URL;
  if (redisUrl) {
    try {
      const Redis = (await import('ioredis')).default;
      kvClient = new Redis(redisUrl);
      console.log('✓ Using direct Redis connection for forum posts (persistent storage)');
      
      // Test connection
      await kvClient.ping();
      return;
    } catch (e) {
      console.log('⚠ Redis connection failed:', e);
      kvClient = null;
    }
  }
  
  if (!kvClient) {
    console.log('⚠ No persistent storage configured for forum posts, using in-memory storage (data won\'t persist)');
  }
}

// Helper functions to get/set forum posts
async function getForumPosts(): Promise<ForumPost[]> {
  await initKV();
  if (kvClient) {
    try {
      let posts: any = await kvClient.get('forum_posts');
      
      // Parse JSON if using direct Redis (stored as string)
      if (typeof posts === 'string') {
        try {
          posts = JSON.parse(posts);
        } catch (e) {
          posts = null;
        }
      }
      
      return posts || inMemoryForumPosts;
    } catch (error) {
      console.error('Error reading forum posts from Redis/KV:', error);
      return inMemoryForumPosts;
    }
  }
  return inMemoryForumPosts;
}

async function saveForumPosts(posts: ForumPost[]): Promise<void> {
  await initKV();
  if (kvClient) {
    try {
      // Check if using direct Redis (ioredis) or Vercel KV
      if (typeof kvClient.set === 'function') {
        // Direct Redis - store as JSON string
        await kvClient.set('forum_posts', JSON.stringify(posts));
      } else {
        // Vercel KV
        await kvClient.set('forum_posts', posts);
      }
    } catch (error) {
      console.error('Error saving forum posts to Redis/KV:', error);
    }
  } else {
    inMemoryForumPosts = posts;
  }
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
    // Return all forum posts
    try {
      const posts = await getForumPosts();
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

      return res.status(400).json({ error: 'Invalid action' });
    } catch (error) {
      return res.status(400).json({ error: 'Invalid request body' });
    }
  }

  if (req.method === 'DELETE') {
    // Delete a forum post
    try {
      const { postId } = req.body;
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
      return res.status(400).json({ error: 'Invalid request body' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}

