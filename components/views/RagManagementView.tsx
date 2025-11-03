import React, { useState } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { RagEntry, AutoResponse } from '../../types';
import { SparklesIcon, DatabaseIcon, TrashIcon } from '../icons';

const RagEntryCard: React.FC<{ entry: RagEntry; onDelete: () => void; onEdit: () => void; }> = ({ entry, onDelete, onEdit }) => (
  <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 flex flex-col">
    <div className="flex justify-between items-start">
        <h3 className="text-lg font-bold text-primary-400 pr-2 flex-1">{entry.title}</h3>
        <div className="flex gap-2">
            <button onClick={onEdit} className="p-1 rounded-full hover:bg-blue-500/20 text-gray-500 hover:text-blue-400 transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
            </button>
            <button onClick={onDelete} className="p-1 rounded-full hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-colors">
                <TrashIcon className="w-5 h-5" />
            </button>
        </div>
    </div>
    <p className="text-gray-300 mt-2 text-sm flex-grow">{entry.content}</p>
    <div className="mt-4">
      {entry.keywords.map(kw => (
        <span key={kw} className="inline-block bg-gray-700 rounded-full px-3 py-1 text-xs font-semibold text-gray-300 mr-2 mb-2">
          {kw}
        </span>
      ))}
    </div>
    <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-700/50">
      <span>Created by {entry.createdBy} on {new Date(entry.createdAt).toLocaleDateString()}</span>
    </div>
  </div>
);

const AutoResponseCard: React.FC<{ response: AutoResponse; onDelete: () => void; onEdit: () => void; }> = ({ response, onDelete, onEdit }) => (
    <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 flex flex-col">
         <div className="flex justify-between items-start">
            <h3 className="text-lg font-bold text-primary-400 pr-2 flex-1">{response.name}</h3>
            <div className="flex gap-2">
                <button onClick={onEdit} className="p-1 rounded-full hover:bg-blue-500/20 text-gray-500 hover:text-blue-400 transition-colors">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                </button>
                <button onClick={onDelete} className="p-1 rounded-full hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-colors">
                    <TrashIcon className="w-5 h-5" />
                </button>
            </div>
        </div>
        <p className="text-gray-300 mt-2 text-sm italic flex-grow">"{response.responseText}"</p>
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
    const { ragEntries, setRagEntries, autoResponses, setAutoResponses } = useMockData();
    const [searchTerm, setSearchTerm] = useState('');
    const [activeTab, setActiveTab] = useState<'RAG' | 'Auto'>('RAG');
    
    const [showNewAutoForm, setShowNewAutoForm] = useState(false);
    const [newAutoResponse, setNewAutoResponse] = useState({ name: '', responseText: '', triggerKeywords: '' });

    const [showNewRagForm, setShowNewRagForm] = useState(false);
    const [newRagEntry, setNewRagEntry] = useState({ title: '', content: '', keywords: '' });
    
    const [editingRag, setEditingRag] = useState<RagEntry | null>(null);
    const [editingAuto, setEditingAuto] = useState<AutoResponse | null>(null);


    const filteredRagEntries = ragEntries.filter(entry => 
        entry.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.keywords.some(kw => kw.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    
    const filteredAutoResponses = autoResponses.filter(resp => 
        resp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resp.responseText.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resp.triggerKeywords.some(kw => kw.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const handleSaveNewAutoResponse = (e: React.FormEvent) => {
        e.preventDefault();
        const newEntry: AutoResponse = {
            id: `AR-${Date.now()}`,
            name: newAutoResponse.name,
            responseText: newAutoResponse.responseText,
            triggerKeywords: newAutoResponse.triggerKeywords.split(',').map(k => k.trim()).filter(Boolean),
            createdAt: new Date().toISOString()
        };
        setAutoResponses(prev => [...prev, newEntry]);
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
        if (window.confirm('Are you sure you want to delete this RAG entry? This cannot be undone.')) {
            setRagEntries(prev => prev.filter(entry => entry.id !== id));
        }
    };

    const handleDeleteAutoResponse = (id: string) => {
        if (window.confirm('Are you sure you want to delete this auto-response?')) {
            setAutoResponses(prev => prev.filter(response => response.id !== id));
        }
    };

    const handleEditRag = (entry: RagEntry) => {
        setEditingRag(entry);
    };

    const handleSaveEditRag = (e: React.FormEvent) => {
        e.preventDefault();
        if (editingRag) {
            setRagEntries(prev => prev.map(entry => 
                entry.id === editingRag.id ? editingRag : entry
            ));
            setEditingRag(null);
        }
    };

    const handleEditAuto = (response: AutoResponse) => {
        setEditingAuto(response);
    };

    const handleSaveEditAuto = (e: React.FormEvent) => {
        e.preventDefault();
        if (editingAuto) {
            setAutoResponses(prev => prev.map(resp => 
                resp.id === editingAuto.id ? editingAuto : resp
            ));
            setEditingAuto(null);
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
            
            {editingAuto && activeTab === 'Auto' && (
                <form onSubmit={handleSaveEditAuto} className="bg-gray-800 p-4 rounded-lg shadow-md border border-blue-600 space-y-4 animate-fade-in">
                    <h3 className="text-lg font-bold text-blue-400">Edit Auto-Response</h3>
                    <input type="text" placeholder="Response Name" value={editingAuto.name} onChange={e => setEditingAuto({...editingAuto, name: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <textarea placeholder="Bot's response text..." value={editingAuto.responseText} onChange={e => setEditingAuto({...editingAuto, responseText: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" rows={3}/>
                    <input type="text" placeholder="Trigger keywords (comma separated)" value={editingAuto.triggerKeywords.join(', ')} onChange={e => setEditingAuto({...editingAuto, triggerKeywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean)})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setEditingAuto(null)} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded">Update Response</button>
                    </div>
                </form>
            )}

            {showNewAutoForm && activeTab === 'Auto' && !editingAuto && (
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

            {editingRag && activeTab === 'RAG' && (
                <form onSubmit={handleSaveEditRag} className="bg-gray-800 p-4 rounded-lg shadow-md border border-blue-600 space-y-4 animate-fade-in">
                    <h3 className="text-lg font-bold text-blue-400">Edit Knowledge Base Entry</h3>
                    <input type="text" placeholder="Entry Title" value={editingRag.title} onChange={e => setEditingRag({...editingRag, title: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <textarea placeholder="Detailed content / solution..." value={editingRag.content} onChange={e => setEditingRag({...editingRag, content: e.target.value})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" rows={5}/>
                    <input type="text" placeholder="Keywords (comma separated)" value={editingRag.keywords.join(', ')} onChange={e => setEditingRag({...editingRag, keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean)})} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setEditingRag(null)} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded">Update Entry</button>
                    </div>
                </form>
            )}

            {showNewRagForm && activeTab === 'RAG' && !editingRag && (
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
                    {filteredRagEntries.map(entry => <RagEntryCard key={entry.id} entry={entry} onDelete={() => handleDeleteRagEntry(entry.id)} onEdit={() => handleEditRag(entry)} />)}
                </div>
            ) : (
                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredAutoResponses.map(resp => <AutoResponseCard key={resp.id} response={resp} onDelete={() => handleDeleteAutoResponse(resp.id)} onEdit={() => handleEditAuto(resp)} />)}
                </div>
            )}
        </div>
    );
};

export default RagManagementView;
