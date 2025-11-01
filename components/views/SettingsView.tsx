import React, { useState } from 'react';

const SettingsView: React.FC = () => {
    const [systemPrompt, setSystemPrompt] = useState<string>(
`You are an expert support bot for a complex scripting application called "Revolution Macro".
Your primary goal is to resolve user issues with friendly, accurate, and easy-to-understand solutions.

Core Instructions:
1.  You are an expert at understanding user intent, even if they use poor grammar, slang, or have spelling mistakes. Always try to understand the underlying question.
2.  Your tone should be helpful and patient. Start your responses in a friendly manner.
3.  First, check for simple keywords to see if an auto-response can solve the issue instantly.
4.  If no auto-response matches, use the provided RAG (knowledge base) documents to formulate a detailed response.
5.  If the RAG context does not contain a relevant solution, politely state that you couldn't find an answer and that you are flagging the post for a human support agent.
6.  When a post is resolved by a human, you may be asked to analyze the conversation to create a new RAG entry. Your goal is to make the knowledge base smarter over time.`
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
                    This prompt defines the core behavior and personality of the support bot. It guides the AI in how to interact with users and handle support requests for Revolution Macro.
                </p>
                <textarea
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    rows={12}
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
