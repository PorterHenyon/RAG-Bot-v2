import { GoogleGenAI, Type } from "@google/genai";
import type { Message, RagEntry, AutoResponse } from '../types';

// This is a MOCK service. In a real application, you would implement actual API calls.
// The API key is assumed to be set in the environment variables.
// const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const MOCK_LATENCY = 1500;

export const geminiService = {
  getAutoResponse: (query: string, autoResponses: AutoResponse[]): AutoResponse | null => {
    const queryWords = new Set(query.toLowerCase().split(/\s+/).filter(w => w.length > 2));
    for (const response of autoResponses) {
        for (const keyword of response.triggerKeywords) {
            if (query.toLowerCase().includes(keyword)) {
                return response;
            }
        }
    }
    return null;
  },

  summarizeConversation: async (conversation: Message[]): Promise<string> => {
    console.log("Simulating Gemini API call for summarization...");
    await new Promise(resolve => setTimeout(resolve, MOCK_LATENCY));
    const userQuery = conversation.find(m => m.author === 'User')?.content || "the user's issue";
    return `The user is experiencing an issue related to "${userQuery.substring(0, 30)}...". They have tried basic troubleshooting steps. The core problem seems to be a configuration error in their settings file.`;
  },

  analyzeAndCreateRagEntry: async (conversation: Message[]): Promise<Omit<RagEntry, 'id' | 'createdAt' | 'createdBy'>> => {
    console.log("Simulating Gemini API call for RAG entry creation...");
    await new Promise(resolve => setTimeout(resolve, MOCK_LATENCY + 500));
    const userQuery = conversation.find(m => m.author === 'User')?.content || "a specific issue";
     return {
      title: `Fix for "${userQuery.substring(0, 20)}..." Error`,
      content: `When a user encounters the error "${userQuery.substring(0, 30)}...", the solution is to navigate to the settings file and ensure the 'enable_beta_features' flag is set to false. Then, restart the application. This resolves the conflict.`,
      keywords: ['error', 'fix', 'settings', 'configuration', 'crash'],
    };
  },
  
  classifyIssue: async (firstMessage: string): Promise<'User Error' | 'Macro Issue'> => {
    console.log("Simulating Gemini API call for issue classification...");
    await new Promise(resolve => setTimeout(resolve, MOCK_LATENCY - 1000));
    if (firstMessage.toLowerCase().includes('crash') || firstMessage.toLowerCase().includes('bug') || firstMessage.toLowerCase().includes('broken')) {
      return 'Macro Issue';
    }
    return 'User Error';
  },

  findRelevantRagEntries: (query: string, allEntries: RagEntry[]): RagEntry[] => {
    const queryWords = new Set(query.toLowerCase().split(/\s+/).filter(w => w.length > 2));
    const scoredEntries = allEntries.map(entry => {
        let score = 0;
        const entryTitle = entry.title.toLowerCase();
        const entryContent = entry.content.toLowerCase();
        const entryKeywords = entry.keywords.join(' ').toLowerCase();

        for (const word of queryWords) {
            if (entryTitle.includes(word)) score += 5;
            if (entryContent.includes(word)) score += 1;
            if (entryKeywords.includes(word)) score += 3;
        }
        return { entry, score };
    });

    return scoredEntries.filter(e => e.score > 0).sort((a, b) => b.score - a.score).map(e => e.entry).slice(0, 2);
  },

  generateBotResponse: async (query: string, contextEntries: RagEntry[]): Promise<string> => {
    console.log("Simulating Gemini API call for bot response...");
    await new Promise(resolve => setTimeout(resolve, MOCK_LATENCY));
    if (contextEntries.length > 0) {
      return `Based on our documentation for "${contextEntries[0].title}", here's what I found: ${contextEntries[0].content}. Does this solve your issue?`;
    } else {
      return "I'm sorry, I couldn't find any specific information about that in my knowledge base. Could you please provide more details? I can escalate this to a human agent if you'd like.";
    }
  },
};
