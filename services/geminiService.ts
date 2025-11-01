import { GoogleGenAI, Type } from "@google/genai";
import type { Message, RagEntry, AutoResponse } from '../types';

// The API key is assumed to be set in the environment variables.
// fix: Use `process.env.API_KEY` for the API key as per the guidelines.
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const geminiService = {
  // This is local logic, no API call needed.
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
    console.log("Calling Gemini API for summarization...");
    try {
        const conversationText = conversation.map(m => `${m.author}: ${m.content}`).join('\n');
        const prompt = `Summarize the following support conversation into a concise paragraph that explains the user's problem and the final solution. This will be used for a knowledge base article. \n\nConversation:\n${conversationText}`;

        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: prompt,
        });

        return response.text;
    } catch (error) {
        console.error("Error summarizing conversation:", error);
        return "There was an error summarizing the conversation. Please try again.";
    }
  },

  analyzeAndCreateRagEntry: async (conversation: Message[]): Promise<Omit<RagEntry, 'id' | 'createdAt' | 'createdBy'>> => {
    console.log("Calling Gemini API for RAG entry creation...");
    try {
        const conversationText = conversation.map(m => `${m.author}: ${m.content}`).join('\n');
        const prompt = `Analyze the following support conversation and generate a structured knowledge base entry from it.
        - The "title" should be a clear, concise summary of the problem (e.g., "Fix for '...' Error").
        - The "content" should be a detailed explanation of the solution.
        - The "keywords" should be an array of relevant search terms.

        Conversation:\n${conversationText}`;

        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        title: { type: Type.STRING },
                        content: { type: Type.STRING },
                        keywords: {
                            type: Type.ARRAY,
                            items: { type: Type.STRING }
                        }
                    },
                    required: ['title', 'content', 'keywords'],
                }
            }
        });
        
        const jsonString = response.text.trim();
        return JSON.parse(jsonString);

    } catch (error) {
        console.error("Error creating RAG entry:", error);
        // Return a default error structure
        return {
            title: "Error Generating Entry",
            content: "The AI failed to generate a RAG entry from this conversation.",
            keywords: ["error"],
        };
    }
  },
  
  classifyIssue: async (firstMessage: string): Promise<'User Error' | 'Macro Issue'> => {
    console.log("Calling Gemini API for issue classification...");
    try {
        const prompt = `Classify the following user issue as either "User Error" or "Macro Issue". Only return one of these two options as a JSON object with a single "classification" key. Issue: "${firstMessage}"`;
        
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        classification: {
                            type: Type.STRING,
                            enum: ['User Error', 'Macro Issue']
                        }
                    },
                    required: ['classification']
                }
            }
        });
        
        const jsonString = response.text.trim();
        const parsed = JSON.parse(jsonString);
        return parsed.classification;
    } catch (error) {
        console.error("Error classifying issue:", error);
        return 'User Error'; // Default fallback
    }
  },

  // This is local logic for scoring, no API call needed.
  findRelevantRagEntries: (query: string, allEntries: RagEntry[]): Array<{ entry: RagEntry, score: number }> => {
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

    return scoredEntries.filter(e => e.score > 0).sort((a, b) => b.score - a.score);
  },

  generateBotResponse: async (query: string, contextEntries: RagEntry[]): Promise<string> => {
    console.log("Calling Gemini API for bot response...");
    try {
        const contextText = contextEntries.map(entry => `Title: ${entry.title}\nContent: ${entry.content}`).join('\n\n');
        const prompt = `You are an expert support bot. A user has the following question: "${query}".
        
        Using the following context from the knowledge base, provide a helpful and friendly answer. If the context doesn't seem to perfectly match, you can say "Based on our documentation for '${contextEntries[0].title}', here's what I found:" before giving the answer.

        Context:\n${contextText}`;

        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: prompt,
        });

        return response.text;
    } catch (error) {
        console.error("Error generating bot response:", error);
        return "I'm sorry, I encountered an error trying to generate a response. A human will be with you shortly.";
    }
  },
};