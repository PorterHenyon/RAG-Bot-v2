import React, { useState, useMemo } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { SlashCommand, CommandParameter } from '../../types';
import { TerminalIcon, XMarkIcon } from '../icons';

const ParameterPill: React.FC<{ param: CommandParameter }> = ({ param }) => (
  <div className={`flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${param.required ? 'bg-red-500/20 text-red-300' : 'bg-gray-700 text-gray-300'}`}>
    <span className="font-mono">{param.name}</span>
    <span className="text-gray-400 mx-1.5 font-sans">:</span>
    <span className="font-medium text-primary-400">{param.type}</span>
  </div>
);

const SlashCommandCard: React.FC<{ command: SlashCommand; onDelete: (id: string) => void }> = ({ command, onDelete }) => (
  <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700 flex flex-col">
    <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
            <TerminalIcon className="w-6 h-6 text-gray-400" />
            <h3 className="text-lg font-bold text-primary-400 font-mono">/{command.name}</h3>
        </div>
        <button 
            onClick={() => onDelete(command.id)} 
            className="text-red-400 hover:text-red-300 transition-colors p-1"
            title="Delete command"
        >
            <XMarkIcon className="w-5 h-5" />
        </button>
    </div>
    <p className="text-gray-300 mt-2 text-sm flex-grow">{command.description}</p>
    {command.parameters.length > 0 && (
        <div className="mt-4">
            <h4 className="text-xs font-semibold text-gray-500 mb-2">PARAMETERS</h4>
            <div className="flex flex-wrap gap-2">
                {command.parameters.map(p => <ParameterPill key={p.name} param={p} />)}
            </div>
        </div>
    )}
     <div className="text-xs text-gray-500 mt-4 pt-2 border-t border-gray-700/50">
      <span>Created on {new Date(command.createdAt).toLocaleDateString()}</span>
    </div>
  </div>
);

const SlashCommandsView: React.FC = () => {
    const { slashCommands, setSlashCommands } = useMockData();
    const [searchTerm, setSearchTerm] = useState('');
    const [showNewCommandForm, setShowNewCommandForm] = useState(false);

    const initialParamState: CommandParameter = { name: '', description: '', type: 'string', required: false };
    const initialCommandState = { name: '', description: '', parameters: [initialParamState] };

    const [newCommand, setNewCommand] = useState(initialCommandState);

    const filteredCommands = useMemo(() => {
        return slashCommands.filter(cmd => 
            cmd.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            cmd.description.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [slashCommands, searchTerm]);

    const handleParamChange = (index: number, field: keyof CommandParameter, value: string | boolean) => {
        const updatedParams = newCommand.parameters.map((p, i) => {
            if (i === index) {
                return { ...p, [field]: value };
            }
            return p;
        });
        setNewCommand({ ...newCommand, parameters: updatedParams });
    };
    
    const addParameter = () => {
        setNewCommand({ ...newCommand, parameters: [...newCommand.parameters, initialParamState] });
    };
    
    const removeParameter = (index: number) => {
        const updatedParams = newCommand.parameters.filter((_, i) => i !== index);
        setNewCommand({ ...newCommand, parameters: updatedParams });
    };

    const handleSaveNewCommand = (e: React.FormEvent) => {
        e.preventDefault();
        const finalCommand: SlashCommand = {
            id: `CMD-${Date.now()}`,
            name: newCommand.name,
            description: newCommand.description,
            parameters: newCommand.parameters.filter(p => p.name.trim() !== ''),
            createdAt: new Date().toISOString()
        };
        setSlashCommands(prev => [finalCommand, ...prev]);
        setNewCommand(initialCommandState);
        setShowNewCommandForm(false);
    };

    const handleDeleteCommand = (id: string) => {
        if (confirm('Are you sure you want to delete this slash command documentation?')) {
            setSlashCommands(prev => prev.filter(cmd => cmd.id !== id));
        }
    };

    return (
        <div className="space-y-6">
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4 text-sm text-blue-200">
                <div className="flex items-start gap-3">
                    <div className="text-blue-400 mt-0.5">ℹ️</div>
                    <div>
                        <strong className="text-blue-100">Note:</strong> Commands are defined in the bot code. 
                        This is just for documentation. 
                        To actually add commands to the bot, edit <code className="bg-blue-950/50 px-1.5 py-0.5 rounded text-xs">bot.py</code>.
                    </div>
                </div>
            </div>
            
            <div className="flex justify-between items-center flex-wrap gap-4">
                <input
                    type="text"
                    placeholder="Search commands..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full md:w-1/2 bg-gray-700 text-white placeholder-gray-400 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
                <button onClick={() => setShowNewCommandForm(true)} className="bg-primary-600 hover:bg-primary-500 text-white font-bold py-2 px-4 rounded transition-colors">
                    Add Command Documentation
                </button>
            </div>

            {showNewCommandForm && (
                <form onSubmit={handleSaveNewCommand} className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700 space-y-4 animate-fade-in">
                    <h3 className="text-xl font-bold text-white">New Slash Command</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <input type="text" placeholder="Command Name (e.g., 'kick')" value={newCommand.name} onChange={e => setNewCommand({ ...newCommand, name: e.target.value.toLowerCase().replace(/\s+/g, '-') })} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500" />
                        <textarea placeholder="Command description..." value={newCommand.description} onChange={e => setNewCommand({ ...newCommand, description: e.target.value })} required className="w-full bg-gray-700 rounded p-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 md:col-span-2" rows={2}/>
                    </div>

                    <h4 className="font-semibold text-gray-300 pt-2 border-t border-gray-700">Parameters</h4>
                    {newCommand.parameters.map((param, index) => (
                        <div key={index} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center">
                            <input type="text" placeholder="name" value={param.name} onChange={e => handleParamChange(index, 'name', e.target.value)} className="md:col-span-3 bg-gray-700 rounded p-2 border border-gray-600 text-sm" />
                            <input type="text" placeholder="description" value={param.description} onChange={e => handleParamChange(index, 'description', e.target.value)} className="md:col-span-5 bg-gray-700 rounded p-2 border border-gray-600 text-sm" />
                             <select value={param.type} onChange={e => handleParamChange(index, 'type', e.target.value)} className="md:col-span-2 bg-gray-700 rounded p-2 border border-gray-600 text-sm">
                                <option value="string">string</option>
                                <option value="number">number</option>
                                <option value="boolean">boolean</option>
                                <option value="user">user</option>
                                <option value="channel">channel</option>
                                <option value="role">role</option>
                            </select>
                            <label className="md:col-span-1 flex items-center justify-center gap-2 text-sm text-gray-300">
                                <input type="checkbox" checked={param.required} onChange={e => handleParamChange(index, 'required', e.target.checked)} className="form-checkbox bg-gray-700 border-gray-600 text-primary-500 h-4 w-4" />
                                Req?
                            </label>
                            <button type="button" onClick={() => removeParameter(index)} className="md:col-span-1 bg-red-800/50 hover:bg-red-700/50 text-red-300 p-2 rounded">
                                <XMarkIcon className="w-4 h-4 mx-auto"/>
                            </button>
                        </div>
                    ))}
                    <button type="button" onClick={addParameter} className="text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 font-bold py-2 px-4 rounded w-full">
                        + Add Parameter
                    </button>

                    <div className="flex justify-end gap-2 pt-4 border-t border-gray-700">
                        <button type="button" onClick={() => setShowNewCommandForm(false)} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded">Cancel</button>
                        <button type="submit" className="bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded">Save Command</button>
                    </div>
                </form>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredCommands.map(cmd => <SlashCommandCard key={cmd.id} command={cmd} onDelete={handleDeleteCommand} />)}
            </div>
            
            {filteredCommands.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                    <TerminalIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>Nothing here yet</p>
                </div>
            )}
        </div>
    );
};

export default SlashCommandsView;