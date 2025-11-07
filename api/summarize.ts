import type { VercelRequest, VercelResponse } from '@vercel/node';
import { GoogleGenAI } from '@google/genai';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Get API key from server-side environment variable (NOT exposed to browser)
    const apiKey = process.env.GEMINI_API_KEY;
    
    if (!apiKey) {
      console.error('GEMINI_API_KEY not set in Vercel environment variables');
      return res.status(500).json({ 
        error: 'Failed to generate summary. Please check that GEMINI_API_KEY is set in Vercel environment variables and try again.' 
      });
    }

    const { conversation } = req.body;

    if (!conversation || !Array.isArray(conversation)) {
      return res.status(400).json({ error: 'Invalid conversation data' });
    }

    // Initialize Gemini AI
    const ai = new GoogleGenAI({ apiKey });

    // Format conversation
    const conversationText = conversation
      .map((m: any) => `${m.author}: ${m.content}`)
      .join('\n');

    const prompt = `Summarize the following support conversation into a concise paragraph that explains the user's problem and the final solution. This will be used for a knowledge base article. \n\nConversation:\n${conversationText}`;

    // Generate summary
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });

    const summary = response.text || "There was an error generating the summary. Please try again.";

    return res.status(200).json({ summary });

  } catch (error: any) {
    console.error('Error in summarize API:', error);
    return res.status(500).json({ 
      error: 'Failed to generate summary',
      details: error.message 
    });
  }
}

