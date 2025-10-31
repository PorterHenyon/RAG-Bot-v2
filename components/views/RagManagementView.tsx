
import React, { useState } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { RagEntry } from '../../types';

const RagEntryCard: React.FC<{ entry: RagEntry }> = ({ entry }) => (
  <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700">
    <h3 className="text-lg font-bold text-primary-400">{entry.title}</h3>
    <p className="text-gray-300 mt-2 text-sm">{entry.content}</p>
    <div className="mt-4">
      {entry.keywords.map(kw => (
        <span key={kw} className="inline-block bg-gray-700 rounded-full px-3 py-1 text-xs font-semibold text-gray-300 mr-2 mb-2">
          {kw}
        </span>
      ))}
    </div>
    <div className="text-xs text-gray-500 mt-2">
      <span>Created by {entry.createdBy} on {new Date(entry.createdAt).toLocaleDateString()}</span>
    </div>
  </div>
);


const RagManagementView: React.FC = () => {
    const { ragEntries } = useMockData();
    const [searchTerm, setSearchTerm] = useState('');

    const filteredEntries = ragEntries.filter(entry => 
        entry.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.keywords.some(kw => kw.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                 <input
                    type="text"
                    placeholder="Search RAG entries..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full md:w-1/2 bg-gray-700 text-white placeholder-gray-400 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <button className="bg-primary-600 hover:bg-primary-500 text-white font-bold py-2 px-4 rounded transition-colors">
                    Add New Entry
                </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredEntries.map(entry => <RagEntryCard key={entry.id} entry={entry} />)}
            </div>
        </div>
    );
};

export default RagManagementView;
   