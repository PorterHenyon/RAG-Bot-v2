// Service for syncing data with the API
import type { RagEntry, AutoResponse, SlashCommand, BotSettings, PendingRagEntry } from '../types';

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

// Cache ETag to enable conditional requests
let cachedDataEtag: string | null = null;
let cachedData: any = null;

export const dataService = {
  async fetchData(): Promise<{ ragEntries: RagEntry[]; autoResponses: AutoResponse[]; slashCommands: SlashCommand[]; botSettings: BotSettings; pendingRagEntries: PendingRagEntry[] }> {
    try {
      const headers: HeadersInit = {};
      
      // Add conditional request header if we have cached ETag
      if (cachedDataEtag) {
        headers['If-None-Match'] = cachedDataEtag;
      }
      
      const response = await fetch(API_URL, { headers });
      
      // If data hasn't changed (304 Not Modified), return cached data
      if (response.status === 304) {
        console.log('✓ Data unchanged, using cache (saved bandwidth)');
        return cachedData;
      }
      
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.statusText}`);
      }
      
      // Store ETag for next request
      const etag = response.headers.get('ETag');
      if (etag) {
        cachedDataEtag = etag;
      }
      
      const data = await response.json();
      cachedData = data; // Cache the data
      
      return data;
    } catch (error) {
      console.error('Error fetching data:', error);
      // Return cached data if available on error
      if (cachedData) {
        console.log('⚠ Using cached data due to error');
        return cachedData;
      }
      throw error;
    }
  },

  async saveData(ragEntries: RagEntry[], autoResponses: AutoResponse[], slashCommands: SlashCommand[], botSettings: BotSettings, pendingRagEntries: PendingRagEntry[]): Promise<void> {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ragEntries, autoResponses, slashCommands, botSettings, pendingRagEntries }),
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

