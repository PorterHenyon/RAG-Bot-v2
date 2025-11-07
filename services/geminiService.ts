import type { Message, RagEntry, AutoResponse } from '../types';

// NOTE: We no longer use the API key client-side for security reasons.
// All AI operations that require the API key are done through secure API endpoints.

export const geminiService = {
  // This is local logic, no API call needed.
  getAutoResponse: (query: string, autoResponses: AutoResponse[]): AutoResponse | null => {
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
    console.log("Calling secure API endpoint for summarization...");
    try {
        const response = await fetch('/api/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ conversation }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to generate summary');
        }

        const data = await response.json();
        return data.summary || "There was an error generating the summary. Please try again.";
    } catch (error: any) {
        console.error("Error summarizing conversation:", error);
        throw new Error(`Failed to generate summary: ${error.message}`);
    }
  },

  analyzeAndCreateRagEntry: async (conversation: Message[]): Promise<Omit<RagEntry, 'id' | 'createdAt' | 'createdBy'>> => {
    console.log("RAG entry analysis (stub - not implemented client-side)");
    // This functionality should be handled by the Discord bot server-side
    // Keeping as a stub for backwards compatibility
    return {
        title: "Manual Entry Required",
        content: "Please create this entry manually or use the Discord bot's automatic RAG creation.",
        keywords: ["manual"],
    };
  },
  
  classifyIssue: async (firstMessage: string): Promise<'User Error' | 'Macro Issue'> => {
    console.log("Issue classification (stub - not implemented client-side)");
    // This functionality is handled by the Discord bot server-side
    // Keeping as a stub for backwards compatibility
    return 'User Error'; // Default fallback
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
    console.log("Bot response generation (stub - not implemented client-side)");
    // This functionality is handled by the Discord bot server-side
    // Keeping as a stub for backwards compatibility
    if (contextEntries.length > 0) {
        return `Based on your query, you might find these articles helpful:\n\n${contextEntries.map(e => `• ${e.title}`).join('\n')}`;
    }
    return "I'm sorry, I couldn't find relevant information. Please try the Discord bot or contact support.";
  },
};