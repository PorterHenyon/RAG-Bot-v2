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

// In-memory storage (for demo - in production, use a database like Supabase, MongoDB, etc.)
// Note: This will reset on each Vercel serverless function restart
// For persistent storage, use a database like Supabase, MongoDB Atlas, or Vercel Postgres
let dataStore: DataStore = {
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
    return res.status(200).json(dataStore);
  }

  if (req.method === 'POST') {
    // Update data
    try {
      const { ragEntries, autoResponses } = req.body as Partial<DataStore>;
      
      if (ragEntries && Array.isArray(ragEntries)) {
        dataStore.ragEntries = ragEntries;
      }
      if (autoResponses && Array.isArray(autoResponses)) {
        dataStore.autoResponses = autoResponses;
      }
      
      return res.status(200).json({ success: true, data: dataStore });
    } catch (error) {
      return res.status(400).json({ error: 'Invalid request body' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
