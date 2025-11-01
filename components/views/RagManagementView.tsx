import React, { useState, useContext, useMemo } from 'react';
import { DataContext } from '../../context/DataContext';
import { RagEntry, AutoResponse } from '../../types';
import { SparklesIcon, DatabaseIcon, XMarkIcon } from '../icons';

const RagEntryCard: React.FC<{ entry: RagEntry; onDelete: (id: string) => void; }> = ({ entry, onDelete }) => (
  <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 relative">
    <button onClick={() => onDelete(entry.id)} className="absolute top-2 right-2 p-1 text-gray-500 hover:text-red-400 hover:bg-gray-700 rounded-full transition-colors">
        <XMarkIcon className="w-5 h-5" />
    </button>
    <h3 className="text-lg font-bold text-primary-400 pr-6">{entry.title}</h3>
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

const AutoResponseCard: React.FC<{ response: AutoResponse; onDelete: (id: string) => void; }> = ({ response, onDelete }) => (
    <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 relative">
        <button onClick={() => onDelete(response.id)} className="absolute top-2 right-2 p-1 text-gray-500 hover:text-red-400 hover:bg-gray-700 rounded-full transition-colors">
            <XMarkIcon className="w-5 h-5" />
        </button>
        <h3 className="text-lg font-bold text-primary-400 pr-6">{response.name}</h3>
        <p className="text-gray-300 mt-2 text-sm italic">"{response.responseText}"</p>
        <div className="mt-4">
            <p className="text-xs text-gray-400 mb-2 font-semibold">TRIGGERS:</p>
            {response.triggerKeywords.map(kw => (
                <span key={kw} className="inline-block bg-gray-700 rounded-full px-3 py-1 text-xs font-semibold text-gray-300 mr-2 mb-2">
                    {kw}
                </span>
            ))}
        </div>
    </div>
);


const RagManagementView: React.FC = () => {
    const { ragEntries, setRagEntries, autoResponses, setAutoResponses } = useContext(DataContext);
    const [searchTerm, setSearchTerm] = useState('');
    const [activeTab, setActiveTab] = useState<'RAG' | 'Auto'>('RAG');
    
    const [showNewAutoForm, setShowNewAutoForm] = useState(false);
    const [newAutoResponse, setNewAutoResponse] = useState({ name: '', responseText: '', triggerKeywords: '' });

    const [showNewRagForm, setShowNewRagForm] = useState(false);
    const [newRagEntry, setNewRagEntry] = useState({ title: '', content: '', keywords: '' });


    const filteredRagEntries = useMemo(() => ragEntries.filter(entry => 
        entry.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.keywords.some(kw => kw.toLowerCase().includes(searchTerm.toLowerCase()))
    ), [ragEntries, searchTerm]);
    
    const filteredAutoResponses = useMemo(() => autoResponses.filter(resp => 
        resp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resp.responseText.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resp.triggerKeywords.some(kw => kw.toLowerCase().includes(searchTerm.toLowerCase()))
    ), [autoResponses, searchTerm]);

    const handleSaveNewAutoResponse = (e: React.FormEvent) => {
        e.preventDefault();
        const newEntry: AutoResponse = {
            id: `AR-${Date.now()}`,
            name: newAutoResponse.name,
            responseText: newAutoResponse.responseText,
            triggerKeywords: newAutoResponse.triggerKeywords.split(',').map(k => k.trim()).filter(Boolean),
            createdAt: new Date().toISOString()
        };
        setAutoResponses(prev => [newEntry, ...prev]);
        setNewAutoResponse({ name: '', responseText: '', triggerKeywords: '' });
        setShowNewAutoForm(false);
    };

    const handleSaveNewRagEntry = (e: React.FormEvent) => {
        e.preventDefault();
        const newEntry: RagEntry = {
            id: `RAG-${Date.now()}`,
            title: newRagEntry.title,
            content: newRagEntry.content,
            keywords: newRagEntry.keywords.split(',').map(k => k.trim()).filter(Boolean),
            createdAt: new Date().toISOString(),
            createdBy: 'Admin', // In a real app, this would be the logged-in user
        };
        setRagEntries(prev => [newEntry, ...prev]);
        setNewRagEntry({ title: '', content: '', keywords: '' });
        setShowNewRagForm(false);
    };
    
    const handleDeleteRagEntry = (id: string) => {
        if (window.confirm('Are you sure you want to delete this knowledge base entry?')) {
            setRagEntries(prev => prev.filter(entry => entry.id !== id));
        }
    };
    
    const handleDeleteAutoResponse = (id: string) => {
        if (window.confirm('Are you sure you want to delete this auto-response?')) {
            setAutoResponses(prev => prev.filter(resp => resp.id !== id));
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center flex-wrap gap-4">
                 <input
                    type="text"
                    placeholder={`Search ${activeTab === 'RAG' ? 'knowledge base...' : 'auto-responses...'}`}
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full md:w-1/2 bg-gray-700 text-white placeholder-gray-400 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <div className="flex items-center gap-2">
                     <button onClick={() => activeTab === 'RAG' ? setShowNewRagForm(true) : setShowNewAutoForm(true)} className="bg-primary-600 hover:bg-primary-500 text-white font-bold py-2 px-4 rounded transition-colors">
                        Add New {activeTab === 'RAG' ? 'Entry' : 'Response'}
                    </button>
                </div>
            </div>

            <div className="flex border-b border-gray-700">
                <button onClick={() => setActiveTab('RAG')} className={`flex items-center gap-2 py-2 px-4 font-semibold ${activeTab === 'RAG' ? 'text-primary-400 border-b-2 border-primary-400' : 'text-gray-400'}`}>
                    <DatabaseIcon className="w-5 h-5" /> Knowledge Base (RAG)
                </button>
                <button onClick={() => setActiveTab('Auto')} className={`flex items-center gap-2 py-2 px-4 font-semibold ${activeTab === 'Auto' ? 'text-primary-400 border-b-2 border-primary-400' : 'text-gray-400'}`}>
                    <SparklesIcon className="w-5 h-5" /> Auto-Responses
                </button>
            </div>
            
            {showNewAutoForm && activeTab === 'Auto' && (
                <form onSubmit={handleSaveNewAutoResponse} className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 space-y-4 animate-fade-in">
                    <h3 className="text-lg font-bold text-white">New Auto-Response</h3>
                    <input type="text" placeholder="Response Name (e.g., 'Password Reset')" value={newAutoResponse.name} onChange={e => setNewAutoResponse({...newAutoResponse, name: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                    <textarea placeholder="Bot's response text..." value={newAutoResponse.responseText} onChange={e => setNewAutoResponse({...newAutoResponse, responseText: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" rows={3}/>
                    <input type="text" placeholder="Trigger keywords, comma, separated" value={newAutoResponse.triggerKeywords} onChange={e => setNewAutoResponse({...newAutoResponse, triggerKeywords: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setShowNewAutoForm(false)} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded">Save</button>
                    </div>
                </form>
            )}

            {showNewRagForm && activeTab === 'RAG' && (
                 <form onSubmit={handleSaveNewRagEntry} className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 space-y-4 animate-fade-in">
                    <h3 className="text-lg font-bold text-white">New Knowledge Base Entry</h3>
                    <input type="text" placeholder="Entry Title (e.g., Fix for 'Failed to Initialize')" value={newRagEntry.title} onChange={e => setNewRagEntry({...newRagEntry, title: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                    <textarea placeholder="Detailed content / solution..." value={newRagEntry.content} onChange={e => setNewRagEntry({...newRagEntry, content: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" rows={5}/>
                    <input type="text" placeholder="Relevant keywords, comma, separated" value={newRagEntry.keywords} onChange={e => setNewRagEntry({...newRagEntry, keywords: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setShowNewRagForm(false)} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded">Save Entry</button>
                    </div>
                </form>
            )}

            {activeTab === 'RAG' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredRagEntries.map(entry => <RagEntryCard key={entry.id} entry={entry} onDelete={handleDeleteRagEntry} />)}
                </div>
            ) : (
                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredAutoResponses.map(resp => <AutoResponseCard key={resp.id} response={resp} onDelete={handleDeleteAutoResponse} />)}
                </div>
            )}
        </div>
    );
};

export default RagManagementView;