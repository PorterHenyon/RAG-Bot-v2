// Service for syncing data with the API
import type { RagEntry, AutoResponse } from '../types';

const API_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api/data`
  : `${window.location.origin}/api/data`;

export const dataService = {
  async fetchData(): Promise<{ ragEntries: RagEntry[]; autoResponses: AutoResponse[] }> {
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

  async saveData(ragEntries: RagEntry[], autoResponses: AutoResponse[]): Promise<void> {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ragEntries, autoResponses }),
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

