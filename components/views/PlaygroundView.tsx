import React, { useState, useRef, useEffect, useContext } from 'react';
import { Message, RagEntry, AutoResponse } from '../../types';
import { DataContext } from '../../context/DataContext';
import { geminiService } from '../../services/geminiService';
import { UserIcon, BotIcon, DatabaseIcon, SparklesIcon } from '../icons';

interface BotContext {
    classification?: string;
    relevantDocs?: RagEntry[];
    autoResponse?: AutoResponse | null;
}

const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const Icon = message.author === 'User' ? UserIcon : BotIcon;
  const isUser = message.author === 'User';
  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : ''}`}>
      {!isUser && <Icon className="w-8 h-8 rounded-full bg-gray-600 p-1 text-white flex-shrink-0" />}
      <div className={`p-3 rounded-lg max-w-lg ${isUser ? 'bg-primary-600 text-white' : 'bg-gray-700 text-gray-200'}`}>
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
       {isUser && <Icon className="w-8 h-8 rounded-full bg-gray-600 p-1 text-white flex-shrink-0" />}
    </div>
  );
};

const PlaygroundView: React.FC = () => {
    const { ragEntries, autoResponses } = useContext(DataContext);
    const [messages, setMessages] = useState<Message[]>([
        { author: 'Bot', content: "Welcome to the Playground! Ask me a question to test my response.", timestamp: new Date().toISOString() }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [botContext, setBotContext] = useState<BotContext | null>(null);

    const chatContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        chatContainerRef.current?.scrollTo({ top: chatContainerRef.current.scrollHeight, behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage: Message = {
            author: 'User',
            content: inputValue,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);
        setBotContext(null);

        // Step 1: Check for an auto-response
        const autoResponse = geminiService.getAutoResponse(userMessage.content, autoResponses);

        let botResponseContent: string;

        if (autoResponse) {
            // Use the canned response
            botResponseContent = autoResponse.responseText;
            setBotContext({ autoResponse });
            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network
        } else {
            // Continue with Gemini AI flow
            const classification = await geminiService.classifyIssue(userMessage.content);
            const relevantDocs = geminiService.findRelevantRagEntries(userMessage.content, ragEntries);
            setBotContext({ classification, relevantDocs });
            botResponseContent = await geminiService.generateBotResponse(userMessage.content, relevantDocs);
        }

        const botMessage: Message = {
            author: 'Bot',
            content: botResponseContent,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
    };

    return (
        <div className="flex h-[calc(100vh-100px)] gap-6">
            {/* Chat Panel */}
            <div className="flex flex-col flex-1 bg-gray-800 rounded-lg shadow-lg">
                <div ref={chatContainerRef} className="flex-1 p-4 overflow-y-auto">
                    {messages.map((msg, index) => <MessageBubble key={index} message={msg} />)}
                     {isLoading && (
                        <div className="flex items-start gap-3 my-4">
                            <BotIcon className="w-8 h-8 rounded-full bg-gray-600 p-1 text-white flex-shrink-0" />
                            <div className="p-3 rounded-lg bg-gray-700">
                                <div className="flex items-center justify-center space-x-1">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse [animation-delay:-0.3s]"></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse [animation-delay:-0.15s]"></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
                <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-700">
                    <div className="flex items-center bg-gray-700 rounded-lg">
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Ask the bot a question..."
                            className="w-full bg-transparent text-white placeholder-gray-400 px-4 py-2 focus:outline-none"
                            disabled={isLoading}
                        />
                        <button type="submit" className="bg-primary-600 hover:bg-primary-500 text-white font-bold py-2 px-4 rounded-r-lg disabled:bg-gray-600 disabled:cursor-not-allowed" disabled={isLoading || !inputValue.trim()}>
                            Send
                        </button>
                    </div>
                </form>
            </div>

            {/* Context Panel */}
            <aside className="w-96 bg-gray-800 rounded-lg shadow-lg p-4 flex flex-col gap-4 overflow-y-auto">
                <h2 className="text-xl font-bold text-white">Bot's Thought Process</h2>
                {botContext ? (
                    botContext.autoResponse ? (
                        <div className="bg-gray-700/50 p-3 rounded-lg">
                            <h3 className="font-semibold text-primary-400 mb-2 flex items-center gap-2">
                                <SparklesIcon className="w-5 h-5" /> Auto-Response Triggered
                            </h3>
                            <p className="font-bold text-gray-200">{botContext.autoResponse.name}</p>
                            <p className="text-xs text-gray-400 mt-1">Matched keywords in user query.</p>
                        </div>
                    ) : (
                        <>
                            <div className="bg-gray-700/50 p-3 rounded-lg">
                                <h3 className="font-semibold text-primary-400 mb-2">Issue Classification</h3>
                                <p className="text-gray-200">{botContext.classification}</p>
                            </div>
                            <div className="bg-gray-700/50 p-3 rounded-lg flex-1">
                                <h3 className="font-semibold text-primary-400 mb-2">Relevant Knowledge</h3>
                                {botContext.relevantDocs && botContext.relevantDocs.length > 0 ? (
                                    <div className="space-y-3">
                                        {botContext.relevantDocs.map(doc => (
                                            <div key={doc.id} className="border-l-4 border-primary-500 pl-3">
                                                <p className="font-bold text-gray-200">{doc.title}</p>
                                                <p className="text-xs text-gray-400 truncate">{doc.content}</p>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-sm text-gray-400">No relevant documents found in the RAG database.</p>
                                )}
                            </div>
                        </>
                    )
                ) : (
                    <div className="text-center text-gray-400 pt-10">
                         <DatabaseIcon className="w-16 h-16 mx-auto text-gray-600" />
                        <p className="mt-4">Ask a question to see the bot's analysis here.</p>
                    </div>
                )}
                 <button 
                    className="w-full mt-auto bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded text-sm transition-colors"
                    onClick={() => alert("This would open a form to create a new RAG entry or Auto-Response based on your question.")}
                >
                    Improve Response
                </button>
            </aside>
        </div>
    );
};

export default PlaygroundView;