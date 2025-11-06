import React, { useState } from 'react';
import { useMockData } from '../../hooks/useMockData';

const SettingsView: React.FC = () => {
    const { botSettings, setBotSettings } = useMockData();
    const [localPrompt, setLocalPrompt] = useState(botSettings.systemPrompt);
    const [saved, setSaved] = useState(false);

    // Sync local prompt with botSettings when it changes
    React.useEffect(() => {
        setLocalPrompt(botSettings.systemPrompt);
    }, [botSettings.systemPrompt]);

    const handleSave = () => {
        // Update the bot settings with new prompt and current timestamp
        setBotSettings({
            systemPrompt: localPrompt,
            updatedAt: new Date().toISOString()
        });
        
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-white mb-4">🤖 Bot Instructions</h2>
                <p className="text-gray-400 mb-4">
                    This controls how the bot responds to users. Changes sync automatically via the API.
                </p>
                <div className="mb-4 p-3 bg-blue-900/30 border border-blue-700/50 rounded-md text-sm text-blue-200">
                    <strong className="text-blue-100">Tip:</strong> Use <code className="bg-blue-950/50 px-1.5 py-0.5 rounded text-xs">/reload</code> in Discord after saving to update the bot immediately.
                </div>
                <textarea
                    value={localPrompt}
                    onChange={(e) => setLocalPrompt(e.target.value)}
                    rows={16}
                    className="w-full bg-gray-900 text-gray-200 p-4 rounded-md border border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-shadow font-mono text-sm"
                    placeholder="Enter the system instruction for the AI bot..."
                />
                <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                        Last updated: {new Date(botSettings.updatedAt).toLocaleString()}
                    </span>
                    <div className="flex items-center gap-4">
                        {saved && <span className="text-green-400 font-semibold animate-fade-in">✓ Saved & synced to API!</span>}
                        <button
                            onClick={handleSave}
                            className="bg-primary-600 hover:bg-primary-500 text-white font-bold py-2 px-6 rounded transition-colors"
                        >
                            Save Instruction
                        </button>
                    </div>
                </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-white mb-4">Bot Status</h2>
                 <p className="text-gray-400 mb-4">
                    The dashboard connects to your bot. Make sure your bot is running from your server or terminal.
                </p>
                <div className="flex items-center space-x-4 p-4 bg-gray-700/50 rounded-md">
                    <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="font-semibold text-green-400">Connected</span>
                </div>
                 <div className="text-xs text-gray-500 mt-4">
                    Note: API keys are managed as environment variables.
                </div>
            </div>

        </div>
    );
};

export default SettingsView;
export default SettingsView;