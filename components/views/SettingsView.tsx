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
                <h2 className="text-2xl font-bold text-white mb-4">🤖 AI System Instruction</h2>
                <p className="text-gray-400 mb-4">
                    This is the core instruction that defines how the Revolution Macro support bot responds to users. It controls the bot's personality, knowledge, and behavior. Changes are synced to the bot automatically via the API.
                </p>
                <div className="mb-4 p-3 bg-blue-900/30 border border-blue-700/50 rounded-md text-sm text-blue-200">
                    <strong className="text-blue-100">💡 Tip:</strong> The bot fetches this instruction from the API when responding. After saving, use <code className="bg-blue-950/50 px-1.5 py-0.5 rounded text-xs">/reload</code> in Discord to update the bot immediately, or wait for the next hourly sync.
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
                <h2 className="text-2xl font-bold text-white mb-4">Bot Configuration</h2>
                 <p className="text-gray-400 mb-4">
                    This dashboard connects to your Discord bot, but it doesn't run the bot's code itself. You need to run your bot from your server or development environment (like PyCharm's terminal) for it to come online and for this dashboard to function correctly.
                </p>
                <div className="flex items-center space-x-4 p-4 bg-gray-700/50 rounded-md">
                    <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="font-semibold text-green-400">Bot is connected and operational.</span>
                </div>
                 <div className="text-xs text-gray-500 mt-4">
                    Note: Your Discord and Gemini API keys should be managed as secure server-side environment variables, not here.
                </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold text-white mb-4">Sharing Your Dashboard</h2>
                 <p className="text-gray-400 mb-4">
                    To share this dashboard with others, you need to "deploy" it to a cloud hosting service. This will give you a public, shareable link that anyone can access in their browser.
                </p>
                <div className="bg-gray-700/50 p-4 rounded-md">
                    <h3 className="font-semibold text-primary-400 mb-2">Recommended Steps:</h3>
                    <ol className="list-decimal list-inside text-gray-300 space-y-2">
                        <li>
                            Store your project's code on a version control platform like <strong>GitHub</strong>.
                        </li>
                        <li>
                            Choose a web hosting service. Excellent, easy-to-use options with free plans include:
                            <ul className="list-disc list-inside ml-6 mt-1">
                                <li><strong>Vercel</strong></li>
                                <li><strong>Netlify</strong></li>
                            </ul>
                        </li>
                        <li>
                            Sign up for one of those services, connect your GitHub account, and select your project.
                        </li>
                        <li>
                            The service will automatically build and deploy your dashboard, providing you with a public URL (e.g., `https://your-app-name.vercel.app`).
                        </li>
                    </ol>
                </div>
            </div>
        </div>
    );
};

export default SettingsView;