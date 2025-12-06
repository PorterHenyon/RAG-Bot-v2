import React, { useState } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { RagEntry, AutoResponse, PendingRagEntry } from '../../types';
import { SparklesIcon, DatabaseIcon, TrashIcon } from '../icons';

const PendingRagCard: React.FC<{ entry: PendingRagEntry; onApprove: () => void; onReject: () => void; }> = ({ entry, onApprove, onReject }) => (
  <div className="bg-yellow-900/20 p-4 rounded-lg shadow-md border-2 border-yellow-500/50 flex flex-col">
    <div className="flex justify-between items-start">
        <div className="flex-1">
            <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-yellow-400">{entry.title}</h3>
                <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded">Pending Review</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">{entry.source} • Thread ID: {entry.threadId}</p>
        </div>
    </div>
    <p className="text-gray-300 mt-3 text-sm flex-grow">{entry.content}</p>
    <div className="mt-3">
      {entry.keywords.map(kw => (
        <span key={kw} className="inline-block bg-gray-700 rounded-full px-3 py-1 text-xs font-semibold text-yellow-300 mr-2 mb-2">
          {kw}
        </span>
      ))}
    </div>
    <div className="text-xs text-gray-400 mt-3 p-2 bg-gray-800/50 rounded border border-gray-700">
      <div className="font-semibold mb-1">Conversation Preview:</div>
      <div className="max-h-20 overflow-y-auto">{entry.conversationPreview}</div>
    </div>
    <div className="flex gap-3 mt-4 pt-3 border-t border-gray-700">
        <button
            onClick={onApprove}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Approve & Add to KB
        </button>
        <button
            onClick={onReject}
            className="flex-1 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Reject
        </button>
    </div>
    <div className="text-xs text-gray-500 mt-2">
      <span>Created on {new Date(entry.createdAt).toLocaleDateString()}</span>
    </div>
  </div>
);

const RagEntryCard: React.FC<{ entry: RagEntry; onDelete: () => void; onEdit: () => void; }> = ({ entry, onDelete, onEdit }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 flex flex-col">
      <div className="flex justify-between items-start">
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-left flex-1 group"
          >
            <div className="flex items-center gap-2">
              <svg 
                className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <h3 className="text-lg font-bold text-primary-400 pr-2 group-hover:text-primary-300">{entry.title}</h3>
            </div>
          </button>
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
      
      {isExpanded && (
        <p className="text-gray-300 mt-2 text-sm flex-grow">{entry.content}</p>
      )}
      
      <div className="mt-3">
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
};

const AutoResponseCard: React.FC<{ response: AutoResponse; onDelete: () => void; onEdit: () => void; }> = ({ response, onDelete, onEdit }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 flex flex-col">
         <div className="flex justify-between items-start">
            <button 
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-left flex-1 group"
            >
              <div className="flex items-center gap-2">
                <svg 
                  className={`w-4 h-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                <h3 className="text-lg font-bold text-primary-400 pr-2 group-hover:text-primary-300">{response.name}</h3>
              </div>
            </button>
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
        
        {isExpanded && (
          <p className="text-gray-300 mt-2 text-sm italic flex-grow">"{response.responseText}"</p>
        )}
        
        <div className="mt-3">
            <p className="text-xs text-gray-400 mb-2 font-semibold">TRIGGERS:</p>
            {response.triggerKeywords.map(kw => (
                <span key={kw} className="inline-block bg-gray-700 rounded-full px-3 py-1 text-xs font-semibold text-gray-300 mr-2 mb-2">
                    {kw}
                </span>
            ))}
        </div>
    </div>
  );
};


const RagManagementView: React.FC = () => {
    const { ragEntries, setRagEntries, autoResponses, setAutoResponses, pendingRagEntries, setPendingRagEntries } = useMockData();
    const [searchTerm, setSearchTerm] = useState('');
    const [activeTab, setActiveTab] = useState<'RAG' | 'Auto'>('RAG');
    
    // Debug: Log pending entries whenever they change
    React.useEffect(() => {
        console.log('🔍 RagManagementView - pendingRagEntries updated:', pendingRagEntries.length, pendingRagEntries);
    }, [pendingRagEntries]);
    
    const [showNewAutoForm, setShowNewAutoForm] = useState(false);
    const [newAutoResponse, setNewAutoResponse] = useState({ name: '', responseText: '', triggerKeywords: '' });

    const [showNewRagForm, setShowNewRagForm] = useState(false);
    const [newRagEntry, setNewRagEntry] = useState({ title: '', content: '', keywords: '' });
    
    const [editingRag, setEditingRag] = useState<RagEntry | null>(null);
    const [editingRagKeywords, setEditingRagKeywords] = useState('');
    
    const [editingAuto, setEditingAuto] = useState<AutoResponse | null>(null);
    const [editingAutoTriggers, setEditingAutoTriggers] = useState('');


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

    const handleSaveNewAutoResponse = async (e: React.FormEvent) => {
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
        // Immediately save to API
        try {
            const { dataService } = await import('../../services/dataService');
            const currentData = await dataService.fetchData();
            await dataService.saveData(currentData.ragEntries, [...currentData.autoResponses, newEntry], currentData.slashCommands, currentData.botSettings, currentData.pendingRagEntries);
            console.log('✓ New auto-response saved immediately');
        } catch (error) {
            console.error('Failed to save new auto-response:', error);
        }
    };

    const handleSaveNewRagEntry = async (e: React.FormEvent) => {
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
        // Immediately save to API
        try {
            const { dataService } = await import('../../services/dataService');
            const currentData = await dataService.fetchData();
            await dataService.saveData([newEntry, ...currentData.ragEntries], currentData.autoResponses, currentData.slashCommands, currentData.botSettings, currentData.pendingRagEntries);
            console.log('✓ New RAG entry saved immediately');
        } catch (error) {
            console.error('Failed to save new RAG entry:', error);
        }
    };

    const handleDeleteRagEntry = async (id: string) => {
        if (window.confirm('Are you sure you want to delete this RAG entry? This cannot be undone.')) {
            setRagEntries(prev => prev.filter(entry => entry.id !== id));
            // Immediately save to API
            try {
                const { dataService } = await import('../../services/dataService');
                const currentData = await dataService.fetchData();
                const updatedRagEntries = currentData.ragEntries.filter(entry => entry.id !== id);
                await dataService.saveData(updatedRagEntries, currentData.autoResponses, currentData.slashCommands, currentData.botSettings, currentData.pendingRagEntries);
                console.log('✓ RAG entry deleted and saved immediately');
            } catch (error) {
                console.error('Failed to delete RAG entry:', error);
            }
        }
    };

    const handleDeleteAutoResponse = async (id: string) => {
        if (window.confirm('Are you sure you want to delete this auto-response?')) {
            setAutoResponses(prev => prev.filter(response => response.id !== id));
            // Immediately save to API
            try {
                const { dataService } = await import('../../services/dataService');
                const currentData = await dataService.fetchData();
                const updatedAutoResponses = currentData.autoResponses.filter(response => response.id !== id);
                await dataService.saveData(currentData.ragEntries, updatedAutoResponses, currentData.slashCommands, currentData.botSettings, currentData.pendingRagEntries);
                console.log('✓ Auto-response deleted and saved immediately');
            } catch (error) {
                console.error('Failed to delete auto-response:', error);
            }
        }
    };

    const handleEditRag = (entry: RagEntry) => {
        setEditingRag(entry);
        setEditingRagKeywords(entry.keywords.join(', '));
    };

    const handleSaveEditRag = async (e: React.FormEvent) => {
        e.preventDefault();
        if (editingRag) {
            const updatedEntry = {
                ...editingRag,
                keywords: editingRagKeywords.split(',').map(k => k.trim()).filter(Boolean)
            };
            setRagEntries(prev => prev.map(entry => 
                entry.id === editingRag.id ? updatedEntry : entry
            ));
            setEditingRag(null);
            setEditingRagKeywords('');
            // Immediately save to API
            try {
                const { dataService } = await import('../../services/dataService');
                const currentData = await dataService.fetchData();
                const updatedRagEntries = currentData.ragEntries.map(entry => 
                    entry.id === editingRag.id ? updatedEntry : entry
                );
                await dataService.saveData(updatedRagEntries, currentData.autoResponses, currentData.slashCommands, currentData.botSettings, currentData.pendingRagEntries);
                console.log('✓ RAG entry saved immediately');
            } catch (error) {
                console.error('Failed to save RAG entry:', error);
            }
        }
    };

    const handleEditAuto = (response: AutoResponse) => {
        setEditingAuto(response);
        setEditingAutoTriggers(response.triggerKeywords.join(', '));
    };

    const handleSaveEditAuto = async (e: React.FormEvent) => {
        e.preventDefault();
        if (editingAuto) {
            const updatedResponse = {
                ...editingAuto,
                triggerKeywords: editingAutoTriggers.split(',').map(k => k.trim()).filter(Boolean)
            };
            setAutoResponses(prev => prev.map(resp => 
                resp.id === editingAuto.id ? updatedResponse : resp
            ));
            setEditingAuto(null);
            setEditingAutoTriggers('');
            // Immediately save to API
            try {
                const { dataService } = await import('../../services/dataService');
                const currentData = await dataService.fetchData();
                const updatedAutoResponses = currentData.autoResponses.map(resp => 
                    resp.id === editingAuto.id ? updatedResponse : resp
                );
                await dataService.saveData(currentData.ragEntries, updatedAutoResponses, currentData.slashCommands, currentData.botSettings, currentData.pendingRagEntries);
                console.log('✓ Auto-response saved immediately');
            } catch (error) {
                console.error('Failed to save auto-response:', error);
            }
        }
    };

    const handleApprovePendingRag = (pendingEntry: PendingRagEntry) => {
        // Convert pending entry to approved RAG entry
        const newEntry: RagEntry = {
            id: `RAG-${Date.now()}`,
            title: pendingEntry.title,
            content: pendingEntry.content,
            keywords: pendingEntry.keywords,
            createdAt: new Date().toISOString(),
            createdBy: 'Auto-generated',
        };
        // Add to RAG entries
        setRagEntries(prev => [newEntry, ...prev]);
        // Remove from pending
        setPendingRagEntries(prev => prev.filter(p => p.id !== pendingEntry.id));
    };

    const handleRejectPendingRag = (id: string) => {
        if (window.confirm('Are you sure you want to reject this pending entry? It will be permanently deleted.')) {
            setPendingRagEntries(prev => prev.filter(p => p.id !== id));
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
                    <input 
                        type="text" 
                        placeholder="Response Name" 
                        value={editingAuto.name} 
                        onChange={e => setEditingAuto({...editingAuto, name: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                    <textarea 
                        placeholder="Bot's response text..." 
                        value={editingAuto.responseText} 
                        onChange={e => setEditingAuto({...editingAuto, responseText: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                        rows={3}
                    />
                    <input 
                        type="text" 
                        placeholder="Trigger keywords (comma separated, e.g., help, support, info)" 
                        value={editingAutoTriggers} 
                        onChange={e => setEditingAutoTriggers(e.target.value)} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        autoComplete="off"
                    />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => { setEditingAuto(null); setEditingAutoTriggers(''); }} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded">Update Response</button>
                    </div>
                </form>
            )}

            {showNewAutoForm && activeTab === 'Auto' && !editingAuto && (
                <form onSubmit={handleSaveNewAutoResponse} className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 space-y-4 animate-fade-in">
                    <h3 className="text-lg font-bold text-white">New Auto-Response</h3>
                    <input 
                        type="text" 
                        placeholder="Response Name (e.g., 'Password Reset')" 
                        value={newAutoResponse.name} 
                        onChange={e => setNewAutoResponse({...newAutoResponse, name: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" 
                    />
                    <textarea 
                        placeholder="Bot's response text..." 
                        value={newAutoResponse.responseText} 
                        onChange={e => setNewAutoResponse({...newAutoResponse, responseText: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" 
                        rows={3}
                    />
                    <input 
                        type="text" 
                        placeholder="Trigger keywords (comma separated, e.g., reset password, forgot password)" 
                        value={newAutoResponse.triggerKeywords} 
                        onChange={e => setNewAutoResponse({...newAutoResponse, triggerKeywords: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        autoComplete="off"
                    />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setShowNewAutoForm(false)} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded">Save</button>
                    </div>
                </form>
            )}

            {editingRag && activeTab === 'RAG' && (
                <form onSubmit={handleSaveEditRag} className="bg-gray-800 p-4 rounded-lg shadow-md border border-blue-600 space-y-4 animate-fade-in">
                    <h3 className="text-lg font-bold text-blue-400">Edit Knowledge Base Entry</h3>
                    <input 
                        type="text" 
                        placeholder="Entry Title" 
                        value={editingRag.title} 
                        onChange={e => setEditingRag({...editingRag, title: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    />
                    <textarea 
                        placeholder="Detailed content / solution..." 
                        value={editingRag.content} 
                        onChange={e => setEditingRag({...editingRag, content: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" 
                        rows={5}
                    />
                    <input 
                        type="text" 
                        placeholder="Keywords (comma separated, e.g., error, fix, tutorial)" 
                        value={editingRagKeywords} 
                        onChange={e => setEditingRagKeywords(e.target.value)} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        autoComplete="off"
                    />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => { setEditingRag(null); setEditingRagKeywords(''); }} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded">Update Entry</button>
                    </div>
                </form>
            )}

            {showNewRagForm && activeTab === 'RAG' && !editingRag && (
                 <form onSubmit={handleSaveNewRagEntry} className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 space-y-4 animate-fade-in">
                    <h3 className="text-lg font-bold text-white">New Knowledge Base Entry</h3>
                    <input 
                        type="text" 
                        placeholder="Entry Title (e.g., Fix for 'Failed to Initialize')" 
                        value={newRagEntry.title} 
                        onChange={e => setNewRagEntry({...newRagEntry, title: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" 
                    />
                    <textarea 
                        placeholder="Detailed content / solution..." 
                        value={newRagEntry.content} 
                        onChange={e => setNewRagEntry({...newRagEntry, content: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" 
                        rows={5}
                    />
                    <input 
                        type="text" 
                        placeholder="Relevant keywords (comma separated, e.g., error, crash, fix)" 
                        value={newRagEntry.keywords} 
                        onChange={e => setNewRagEntry({...newRagEntry, keywords: e.target.value})} 
                        required 
                        className="w-full bg-gray-700 text-white rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
                        autoComplete="off"
                    />
                    <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setShowNewRagForm(false)} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded">Save Entry</button>
                    </div>
                </form>
            )}

            {activeTab === 'RAG' ? (
                <div className="space-y-6">
                    {/* PENDING SECTION - Discord Bot Entries Awaiting Approval */}
                    {pendingRagEntries && pendingRagEntries.length > 0 ? (
                        <div className="space-y-4 bg-yellow-900/10 p-6 rounded-lg border-2 border-yellow-500/30">
                            <div className="flex items-center gap-3">
                                <svg className="w-7 h-7 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                <div>
                                    <h2 className="text-2xl font-bold text-yellow-400">
                                        📋 Pending Review ({pendingRagEntries.length})
                                    </h2>
                                    <p className="text-sm text-gray-400">
                                        Auto-generated from Discord bot • Approve or reject below
                                    </p>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                                {pendingRagEntries.map(entry => (
                                    <PendingRagCard
                                        key={entry.id}
                                        entry={entry}
                                        onApprove={() => handleApprovePendingRag(entry)}
                                        onReject={() => handleRejectPendingRag(entry.id)}
                                    />
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700 text-center">
                            <svg className="w-12 h-12 text-gray-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <p className="text-gray-400 text-lg font-medium">All clear</p>
                            <p className="text-gray-500 text-sm mt-2">Bot entries show up here when they need review</p>
                        </div>
                    )}

                    {/* APPROVED KNOWLEDGE BASE SECTION - Manual & Approved Entries */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-primary-400 flex items-center gap-2">
                                <DatabaseIcon className="w-7 h-7" />
                                Knowledge Base ({filteredRagEntries.length})
                            </h2>
                            <span className="text-sm text-gray-500">Manual entries & approved bot entries</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredRagEntries.length > 0 ? (
                                filteredRagEntries.map(entry => <RagEntryCard key={entry.id} entry={entry} onDelete={() => handleDeleteRagEntry(entry.id)} onEdit={() => handleEditRag(entry)} />)
                            ) : (
                                <div className="col-span-full bg-gray-800/50 p-8 rounded-lg border border-gray-700 text-center">
                                    <DatabaseIcon className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                                    <p className="text-gray-400 text-lg">Nothing here yet</p>
                                    <p className="text-gray-500 text-sm mt-2">Add entries using the button above</p>
                                </div>
                            )}
                        </div>
                    </div>
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
