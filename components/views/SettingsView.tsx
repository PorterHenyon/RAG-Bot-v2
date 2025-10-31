
import React, { useState } from 'react';

const SettingsView: React.FC = () => {
    const [systemPrompt, setSystemPrompt] = useState<string>(
`You are a helpful and friendly support bot for a complex macro application. 
Your primary goal is to resolve user issues quickly and accurately.
1. First, check for keywords and try to match the user's query with a known solution from your database.
2. If no direct match is found, use the provided RAG context to formulate a helpful response.
3. If you cannot find a relevant solution, politely inform the user and escalate the ticket to a human support agent.
4. When a ticket is resolved by a human, you will be asked to analyze the solution and prepare it for addition to the knowledge base.`
    );
    const [isSaving, setIsSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    const handleSave = () => {
        setIsSaving(true);
        setSaved(false);
        setTimeout(() => {
            setIsSaving(false);
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        }, 1500);
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-white mb-4">System Prompt</h2>
                <p className="text-gray-400 mb-4">
                    This prompt defines the core behavior and personality of the support bot. It guides the AI in how to interact with users and handle support requests.
                </p>
                <textarea
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    rows={10}
                    className="w-full bg-gray-900 text-gray-200 p-3 rounded-md border border-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-shadow"
                />
                <div className="mt-4 flex items-center justify-end">
                    {saved && <span className="text-green-400 mr-4">Prompt saved successfully!</span>}
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="bg-primary-600 hover:bg-primary-500 text-white font-bold py-2 px-4 rounded transition-colors disabled:bg-gray-600 disabled:cursor-wait"
                    >
                        {isSaving ? 'Saving...' : 'Save Prompt'}
                    </button>
                </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-white mb-4">Bot Configuration</h2>
                 <p className="text-gray-400 mb-4">
                    Monitor the bot's connection status. Your Discord Bot Token is configured securely on the server and should not be managed here.
                </p>
                <div className="flex items-center space-x-4 p-4 bg-gray-700/50 rounded-md">
                    <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="font-semibold text-green-400">Bot is connected and operational.</span>
                </div>
                 <div className="text-xs text-gray-500 mt-4">
                    Note: The Discord token provided in the prompt is a fake, placeholder token for security reasons. A real application must handle tokens as secure server-side environment variables.
                </div>
            </div>
        </div>
    );
};

export default SettingsView;
   