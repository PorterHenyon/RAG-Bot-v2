import { VercelRequest, VercelResponse } from '@vercel/node';

// Initialize KV/Redis client
async function initKV() {
  // Try Vercel KV first
  if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
    try {
      const kvModule = await import('@vercel/kv');
      return kvModule.kv;
    } catch (e) {
      console.log('⚠ Vercel KV not available');
    }
  }
  
  // Try direct Redis connection
  const redisUrl = process.env.REDIS_URL || process.env.STORAGE_URL;
  if (redisUrl) {
    try {
      const Redis = (await import('ioredis')).default;
      const client = new Redis(redisUrl);
      await client.ping();
      return client;
    } catch (e) {
      console.log('⚠ Redis connection failed');
    }
  }
  
  return null;
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // Get storage usage info
    try {
      const kvClient = await initKV();
      if (!kvClient) {
        return res.status(200).json({
          error: 'No persistent storage configured',
          message: 'Cannot check storage usage without KV/Redis'
        });
      }

      // Get all keys and calculate sizes
      let totalSize = 0;
      const keySizes: Record<string, number> = {};
      
      if (typeof kvClient.keys === 'function') {
        // Direct Redis - can use KEYS command
        const keys = await kvClient.keys('*');
        for (const key of keys) {
          const value = await kvClient.get(key);
          const size = typeof value === 'string' ? Buffer.byteLength(value, 'utf8') : JSON.stringify(value).length;
          keySizes[key] = size;
          totalSize += size;
        }
      } else {
        // Vercel KV - estimate based on known keys
        const knownKeys = ['rag_entries', 'auto_responses', 'slash_commands', 'bot_settings', 'pending_rag_entries', 'forum_posts', 'leaderboard'];
        for (const key of knownKeys) {
          try {
            const value = await kvClient.get(key);
            if (value) {
              const size = typeof value === 'string' ? Buffer.byteLength(value, 'utf8') : JSON.stringify(value).length;
              keySizes[key] = size;
              totalSize += size;
            }
          } catch (e) {
            // Key doesn't exist
          }
        }
      }

      return res.status(200).json({
        totalSizeBytes: totalSize,
        totalSizeMB: (totalSize / 1024 / 1024).toFixed(2),
        keySizes,
        message: 'Storage usage calculated'
      });
    } catch (error) {
      console.error('Error checking storage:', error);
      return res.status(500).json({ error: 'Failed to check storage usage' });
    }
  }

  if (req.method === 'POST') {
    // Cleanup storage
    try {
      const { action, options } = req.body;
      const kvClient = await initKV();
      
      if (!kvClient) {
        return res.status(400).json({ error: 'No persistent storage configured' });
      }

      if (action === 'cleanup_forum_posts') {
        // Clean up old forum posts
        const retentionDays = options?.retentionDays || 7;
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - retentionDays);

        const forumPosts = await kvClient.get('forum_posts');
        if (forumPosts) {
          const posts = Array.isArray(forumPosts) ? forumPosts : JSON.parse(forumPosts as string);
          const initialCount = posts.length;
          
          // Filter out old solved/closed posts
          const filteredPosts = posts.filter((post: any) => {
            if (post.status === 'Solved' || post.status === 'Closed') {
              const postDate = new Date(post.createdAt || post.updatedAt);
              return postDate > cutoffDate;
            }
            return true; // Keep unsolved posts
          });

          const deletedCount = initialCount - filteredPosts.length;
          
          if (typeof kvClient.set === 'function') {
            await kvClient.set('forum_posts', JSON.stringify(filteredPosts));
          } else {
            await kvClient.set('forum_posts', filteredPosts);
          }

          return res.status(200).json({
            success: true,
            deleted: deletedCount,
            kept: filteredPosts.length,
            message: `Cleaned up ${deletedCount} old forum posts (kept posts newer than ${retentionDays} days)`
          });
        }
      }

      if (action === 'cleanup_pending_rag') {
        // Clear all pending RAG entries
        if (typeof kvClient.set === 'function') {
          await kvClient.set('pending_rag_entries', JSON.stringify([]));
        } else {
          await kvClient.set('pending_rag_entries', []);
        }

        return res.status(200).json({
          success: true,
          message: 'Cleared all pending RAG entries'
        });
      }

      if (action === 'delete_key') {
        // Delete a specific key
        const key = options?.key;
        if (!key) {
          return res.status(400).json({ error: 'Missing key parameter' });
        }

        await kvClient.del(key);
        return res.status(200).json({
          success: true,
          message: `Deleted key: ${key}`
        });
      }

      return res.status(400).json({ error: 'Invalid action' });
    } catch (error) {
      console.error('Error cleaning up storage:', error);
      return res.status(500).json({ error: 'Failed to cleanup storage' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}

