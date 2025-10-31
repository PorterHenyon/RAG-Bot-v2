
import { GoogleGenAI, Type } from "@google/genai";
import type { Message, RagEntry } from '../types';

// This is a MOCK service. In a real application, you would implement actual API calls.
// The API key is assumed to be set in the environment variables.
// const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const MOCK_LATENCY = 1500;

export const geminiService = {
  summarizeConversation: async (conversation: Message[]): Promise<string> => {
    console.log("Simulating Gemini API call for summarization...");
    // In a real app:
    /*
    const prompt = `Summarize the following support conversation:\n\n${conversation.map(m => `${m.author}: ${m.content}`).join('\n')}`;
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });
    return response.text;
    */
    await new Promise(resolve => setTimeout(resolve, MOCK_LATENCY));
    const userQuery = conversation.find(m => m.author === 'User')?.content || "the user's issue";
    return `The user is experiencing an issue related to "${userQuery.substring(0, 30)}...". They have tried basic troubleshooting steps. The core problem seems to be a configuration error in their settings file.`;
  },

  analyzeAndCreateRagEntry: async (conversation: Message[]): Promise<Omit<RagEntry, 'id' | 'createdAt' | 'createdBy'>> => {
    console.log("Simulating Gemini API call for RAG entry creation...");
    // In a real app:
    /*
    const prompt = `Analyze the following resolved support conversation and extract the necessary information to create a knowledge base article for future use. Provide a title, a detailed solution, and relevant keywords. The conversation is:\n\n${conversation.map(m => `${m.author}: ${m.content}`).join('\n')}`;
    const response = await ai.models.generateContent({
        model: "gemini-2.5-flash",
        contents: prompt,
        config: {
            responseMimeType: "application/json",
            responseSchema: {
                type: Type.OBJECT,
                properties: {
                    title: { type: Type.STRING },
                    solution: { type: Type.STRING },
                    keywords: { type: Type.ARRAY, items: { type: Type.STRING } },
                }
            }
        }
    });
    const result = JSON.parse(response.text);
    return { title: result.title, content: result.solution, keywords: result.keywords };
    */
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
    // In a real app:
    /*
     const prompt = `Classify the following user support request as either "User Error" or "Macro Issue".\n\nRequest: "${firstMessage}"\n\nClassification:`;
     const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: prompt
     });
     const classification = response.text.trim();
     if (classification === 'User Error' || classification === 'Macro Issue') {
        return classification;
     }
     return 'User Error'; // Default
    */
    await new Promise(resolve => setTimeout(resolve, MOCK_LATENCY - 500));
    if (firstMessage.toLowerCase().includes('crash') || firstMessage.toLowerCase().includes('bug')) {
      return 'Macro Issue';
    }
    return 'User Error';
  }
};
   