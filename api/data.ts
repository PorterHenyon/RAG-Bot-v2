// Vercel API route for managing RAG data
import type { VercelRequest, VercelResponse } from '@vercel/node';

interface RagEntry {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  createdAt: string;
  createdBy: string;
}

interface AutoResponse {
  id: string;
  name: string;
  triggerKeywords: string[];
  responseText: string;
  createdAt: string;
}

interface DataStore {
  ragEntries: RagEntry[];
  autoResponses: AutoResponse[];
}

// Persistent storage using Vercel KV (Redis)
// Falls back to in-memory if KV not configured
let kvClient: any = null;
let inMemoryStore: DataStore = {
  ragEntries: [
    {
      id: 'RAG-001',
      title: 'Character Resets Instead of Converting Honey',
      content: "This issue typically occurs when the 'Auto-Deposit' setting is enabled, but the main 'Gather' task is not set to pause during the conversion process. The macro incorrectly prioritizes gathering, causing it to reset the character's position and interrupt honey conversion. To fix this, go to Script Settings > Tasks > Gather and check the box 'Pause While Converting Honey'. Alternatively, you can disable 'Auto-Deposit' in the Hive settings.",
      keywords: ['honey', 'pollen', 'convert', 'reset', 'resets', 'resetting', 'gather', 'auto-deposit', 'stuck', 'hive'],
      createdAt: new Date().toISOString(),
      createdBy: 'System',
    },
  ],
  autoResponses: [
    {
      id: 'AR-001',
      name: 'Password Reset',
      triggerKeywords: ['password', 'reset', 'forgot', 'lost account'],
      responseText: 'You can reset your password by visiting this link: [https://revolutionmacro.com/password-reset](https://revolutionmacro.com/password-reset).',
      createdAt: new Date().toISOString(),
    },
  ],
};

// Initialize KV/Redis client if available (lazy import)
async function initKV() {
  if (kvClient) return; // Already initialized
  
  // Try Vercel KV first (REST API)
  if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
    try {
      const kvModule = await import('@vercel/kv');
      kvClient = kvModule.kv;
      console.log('✓ Using Vercel KV for persistent storage');
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
      console.log('✓ Using direct Redis connection for persistent storage');
      
      // Test connection
      await kvClient.ping();
      return;
    } catch (e) {
      console.log('⚠ Redis connection failed:', e);
      kvClient = null;
    }
  }
  
  if (!kvClient) {
    console.log('⚠ No persistent storage configured, using in-memory storage (data won\'t persist)');
  }
}

// Helper functions to get/set data
async function getDataStore(): Promise<DataStore> {
  await initKV();
  if (kvClient) {
    try {
      // Check if using Vercel KV (has .get method) or direct Redis (has .get method)
      let ragEntries: any;
      let autoResponses: any;
      
      if (typeof kvClient.get === 'function') {
        // Direct Redis (ioredis)
        ragEntries = await kvClient.get('rag_entries');
        autoResponses = await kvClient.get('auto_responses');
        
        // Parse JSON if stored as strings
        if (typeof ragEntries === 'string') {
          try {
            ragEntries = JSON.parse(ragEntries);
          } catch (e) {
            console.error('Error parsing rag_entries JSON:', e);
            ragEntries = null;
          }
        }
        if (typeof autoResponses === 'string') {
          try {
            autoResponses = JSON.parse(autoResponses);
          } catch (e) {
            console.error('Error parsing auto_responses JSON:', e);
            autoResponses = null;
          }
        }
      } else {
        // Vercel KV (different API)
        ragEntries = await kvClient.get('rag_entries');
        autoResponses = await kvClient.get('auto_responses');
      }
      
      // Use stored data if available, otherwise fall back to in-memory
      // IMPORTANT: Only use fallback if we have NO persistent storage configured
      // If persistent storage exists but is empty, return empty arrays to avoid confusion
      const hasPersistentStorage = !!kvClient;
      
      let result: DataStore;
      
      if (hasPersistentStorage) {
        // We have persistent storage - use what's stored (even if empty)
        result = {
          ragEntries: (ragEntries && Array.isArray(ragEntries)) ? ragEntries : [],
          autoResponses: (autoResponses && Array.isArray(autoResponses)) ? autoResponses : [],
        };
        
        if (ragEntries && Array.isArray(ragEntries) && ragEntries.length > 0) {
          console.log(`✓ Loaded ${ragEntries.length} RAG entries from persistent storage`);
        } else {
          console.log(`⚠ No RAG entries found in persistent storage (database is empty)`);
        }
        
        if (autoResponses && Array.isArray(autoResponses) && autoResponses.length > 0) {
          console.log(`✓ Loaded ${autoResponses.length} auto-responses from persistent storage`);
        } else {
          console.log(`⚠ No auto-responses found in persistent storage (database is empty)`);
        }
      } else {
        // No persistent storage - use in-memory fallback
        result = {
          ragEntries: (ragEntries && Array.isArray(ragEntries) && ragEntries.length > 0) ? ragEntries : inMemoryStore.ragEntries,
          autoResponses: (autoResponses && Array.isArray(autoResponses) && autoResponses.length > 0) ? autoResponses : inMemoryStore.autoResponses,
        };
        
        console.log(`⚠ Using in-memory fallback data (persistent storage not configured)`);
        console.log(`   ⚠⚠⚠ WARNING: Data will be lost on redeploy! Configure Vercel KV or Redis.`);
      }
      
      return result;
    } catch (error) {
      console.error('Error reading from Redis/KV:', error);
      return inMemoryStore;
    }
  }
  console.log(`⚠ No persistent storage configured, using in-memory store (${inMemoryStore.ragEntries.length} RAG entries, ${inMemoryStore.autoResponses.length} auto-responses)`);
  return inMemoryStore;
}

async function saveDataStore(data: DataStore): Promise<void> {
  await initKV();
  if (kvClient) {
    try {
      // Check if using direct Redis (ioredis) or Vercel KV
      if (typeof kvClient.set === 'function') {
        // Direct Redis - store as JSON strings
        await kvClient.set('rag_entries', JSON.stringify(data.ragEntries));
        await kvClient.set('auto_responses', JSON.stringify(data.autoResponses));
        console.log(`✓ Saved ${data.ragEntries.length} RAG entries and ${data.autoResponses.length} auto-responses to Redis`);
      } else {
        // Vercel KV
        await kvClient.set('rag_entries', data.ragEntries);
        await kvClient.set('auto_responses', data.autoResponses);
        console.log(`✓ Saved ${data.ragEntries.length} RAG entries and ${data.autoResponses.length} auto-responses to Vercel KV`);
      }
    } catch (error) {
      console.error('Error saving to Redis/KV:', error);
      throw error; // Re-throw so caller knows save failed
    }
  } else {
    inMemoryStore = data;
    console.log(`⚠ Saved to in-memory storage (will be lost on restart): ${data.ragEntries.length} RAG entries, ${data.autoResponses.length} auto-responses`);
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // Return all data
    try {
      const data = await getDataStore();
      // Log what we're returning for debugging
      console.log(`📤 GET /api/data returning: ${data.ragEntries.length} RAG entries, ${data.autoResponses.length} auto-responses`);
      return res.status(200).json(data);
    } catch (error) {
      console.error('Error fetching data:', error);
      // Only return inMemoryStore as last resort (when Redis fails)
      console.log(`⚠ Returning fallback in-memory data due to error`);
      return res.status(200).json(inMemoryStore);
    }
  }

  if (req.method === 'POST') {
    // Update data
    try {
      await initKV(); // Ensure KV is initialized before saving
      
      const currentData = await getDataStore();
      const { ragEntries, autoResponses } = req.body as Partial<DataStore>;
      
      // Only update fields that are provided and valid
      const updatedData: DataStore = {
        ragEntries: (ragEntries && Array.isArray(ragEntries)) ? ragEntries : currentData.ragEntries,
        autoResponses: (autoResponses && Array.isArray(autoResponses)) ? autoResponses : currentData.autoResponses,
      };
      
      console.log(`📝 Saving data: ${updatedData.ragEntries.length} RAG entries, ${updatedData.autoResponses.length} auto-responses`);
      
      // Check if we have persistent storage before saving
      if (!kvClient) {
        console.error('❌ CRITICAL: No persistent storage configured! Data will be lost on redeploy.');
        console.error('   Please configure Vercel KV or Redis. See SETUP_VERCEL_KV.md for instructions.');
        // Still save to in-memory as fallback, but warn the user
        await saveDataStore(updatedData);
        return res.status(200).json({ 
          success: true, 
          data: updatedData,
          warning: 'No persistent storage configured. Data saved to memory only and will be lost on redeploy. Please configure Vercel KV or Redis.'
        });
      }
      
      await saveDataStore(updatedData);
      
      // Verify the save by reading back (only if we have persistent storage)
      if (kvClient) {
        const verifyData = await getDataStore();
        if (verifyData.ragEntries.length !== updatedData.ragEntries.length) {
          console.error(`⚠ Data mismatch after save! Expected ${updatedData.ragEntries.length} RAG entries, got ${verifyData.ragEntries.length}`);
          return res.status(500).json({ 
            error: 'Data verification failed after save',
            warning: 'Data may not have persisted correctly'
          });
        } else {
          console.log(`✓ Data verified: ${verifyData.ragEntries.length} RAG entries persisted successfully`);
        }
      }
      
      return res.status(200).json({ success: true, data: updatedData });
    } catch (error) {
      console.error('Error saving data:', error);
      return res.status(500).json({ error: `Failed to save data: ${error instanceof Error ? error.message : 'Unknown error'}` });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
