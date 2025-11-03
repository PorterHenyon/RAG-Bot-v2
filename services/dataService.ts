// Service for syncing data with the API
import type { RagEntry, AutoResponse, SlashCommand, BotSettings } from '../types';

const getApiUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.length > 0) {
    return `${envUrl}/api/data`;
  }
  // Fallback to current origin (works in browser)
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/data`;
  }
  // Server-side fallback
  return '/api/data';
};

const API_URL = getApiUrl();

export const dataService = {
  async fetchData(): Promise<{ ragEntries: RagEntry[]; autoResponses: AutoResponse[]; slashCommands: SlashCommand[]; botSettings: BotSettings }> {
    try {
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching data:', error);
      throw error;
    }
  },

  async saveData(ragEntries: RagEntry[], autoResponses: AutoResponse[], slashCommands: SlashCommand[], botSettings: BotSettings): Promise<void> {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ragEntries, autoResponses, slashCommands, botSettings }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save data: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('Data saved successfully:', result);
    } catch (error) {
      console.error('Error saving data:', error);
      throw error;
    }
  },
};

