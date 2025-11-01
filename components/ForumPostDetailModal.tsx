import React, { useState } from 'react';
import { ForumPost, Message, PostStatus } from '../types';
import { XMarkIcon, UserIcon, BotIcon, SupportIcon, HashtagIcon, SystemIcon } from './icons';
import PostStatusBadge from './PostStatusBadge';
import { geminiService } from '../../services/geminiService';

interface ForumPostDetailModalProps {
  post: ForumPost;
  onClose: () => void;
  onUpdate: (post: ForumPost) => void;
}

const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.author === 'User';
  const isSystem = message.author === 'System';

  if (isSystem) {
      return (
        <div className="flex items-center gap-2 my-4 text-xs text-gray-400 italic">
            <SystemIcon className="w-4 h-4 flex-shrink-0" />
            <span>{message.content}</span>
            <span className="flex-grow border-t border-gray-700 border-dashed"></span>
        </div>
      );
  }
  
  const Icon = isUser ? UserIcon : message.author === 'Bot' ? BotIcon : SupportIcon;
  
  return (
    <div className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : ''}`}>
      {!isUser && <Icon className="w-8 h-8 rounded-full bg-gray-600 p-1 text-white flex-shrink-0" />}
      <div className={`p-3 rounded-lg max-w-md ${isUser ? 'bg-primary-600 text-white' : 'bg-gray-600 text-gray-200'}`}>
        <p className="text-sm">{message.content}</p>
        <p className={`text-xs mt-2 opacity-60 ${isUser ? 'text-right' : 'text-left'}`}>{new Date(message.timestamp).toLocaleTimeString()}</p>
      </div>
       {isUser && <Icon className="w-8 h-8 rounded-full bg-gray-600 p-1 text-white flex-shrink-0" />}
    </div>
  );
};

const ForumPostDetailModal: React.FC<ForumPostDetailModalProps> = ({ post, onClose, onUpdate }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingAction, setProcessingAction] = useState<string | null>(null);

  const handleStatusChange = (newStatus: PostStatus) => {
    onUpdate({ ...post, status: newStatus });
  };
  
  const handleResolveAndClose = () => {
    if (window.confirm('Are you sure you want to close this forum post?')) {
        const systemMessage: Message = { author: 'System', content: `Post marked as closed by an admin.`, timestamp: new Date().toISOString()};
        onUpdate({...post, status: PostStatus.Closed, conversation: [...post.conversation, systemMessage]});
        onClose();
    }
  };

  const handleSummarize = async () => {
    if (post.status !== PostStatus.Resolved) {
        alert("Can only summarize resolved posts.");
        return;
    }
    setIsProcessing(true);
    setProcessingAction('Summarizing');
    const summary = await geminiService.summarizeConversation(post.conversation);
    const summaryMessage: Message = { author: 'Bot', content: `AI Summary: ${summary}`, timestamp: new Date().toISOString()};
    onUpdate({...post, conversation: [...post.conversation, summaryMessage]});
    setIsProcessing(false);
    setProcessingAction(null);
    alert('Summary generated and added to conversation history. Next, you would add this to the RAG database.');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-2xl w-full max-w-4xl h-[90vh] flex flex-col">
        <header className="flex items-center justify-between p-4 border-b border-gray-700 flex-shrink-0">
          <div>
            <h2 className="text-xl font-bold text-white">{post.postTitle}</h2>
            <p className="text-sm text-gray-400">
              Post <span className="font-semibold">{post.id}</span> by {post.user.username}
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-700">
            <XMarkIcon className="w-6 h-6 text-gray-300" />
          </button>
        </header>

        <div className="flex-1 flex overflow-hidden">
          {/* Main Content */}
          <main className="flex-1 p-4 overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-2">Thread</h3>
            <div className="flex flex-col">
              {post.conversation.map((msg, index) => <MessageBubble key={index} message={msg} />)}
            </div>
          </main>

          {/* Sidebar */}
          <aside className="w-80 bg-gray-800/50 border-l border-gray-700 p-4 flex-shrink-0 flex flex-col gap-6 overflow-y-auto">
            <div>
              <h4 className="font-semibold text-gray-300 mb-2">Status</h4>
              <select 
                value={post.status}
                onChange={(e) => handleStatusChange(e.target.value as PostStatus)}
                className="w-full bg-gray-700 text-white border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {Object.values(PostStatus).map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
             <div>
                <h4 className="font-semibold text-gray-300 mb-2">Tags</h4>
                <div className="flex flex-wrap gap-2">
                    {post.tags.map(tag => (
                        <span key={tag} className="bg-gray-700 text-xs text-gray-300 font-semibold px-2 py-1 rounded-full">{tag}</span>
                    ))}
                </div>
            </div>
            
            <div className="border-t border-gray-700 pt-4">
                <h4 className="font-semibold text-gray-300 mb-2">User Info</h4>
                <div className="flex items-center gap-3">
                    <img src={post.user.avatarUrl} alt={post.user.username} className="w-12 h-12 rounded-full" />
                    <div>
                        <p className="font-bold text-white">{post.user.username}</p>
                        <p className="text-xs text-gray-400">ID: {post.user.id}</p>
                    </div>
                </div>
                 <div className="mt-3 flex items-center gap-2 text-gray-400">
                    <HashtagIcon className="w-5 h-5" />
                    <span className="text-sm font-mono">Post ID: {post.postId}</span>
                </div>
            </div>

            <div className="border-t border-gray-700 pt-4">
              <h4 className="font-semibold text-gray-300 mb-2">Admin Actions</h4>
              <div className="flex flex-col gap-2">
                <button 
                    onClick={handleSummarize}
                    disabled={isProcessing || post.status !== PostStatus.Resolved}
                    className="w-full text-left bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded disabled:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                    {isProcessing && processingAction === 'Summarizing' ? 'Summarizing...' : 'Summarize for RAG'}
                </button>
                {post.status === PostStatus.Resolved && (
                     <button 
                        onClick={handleResolveAndClose}
                        disabled={isProcessing}
                        className="w-full text-left bg-red-600 hover:bg-red-500 text-white font-bold py-2 px-4 rounded disabled:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors animate-pulse">
                        Close Post
                    </button>
                )}
              </div>
            </div>

            {post.logs && (
                <div className="border-t border-gray-700 pt-4">
                    <h4 className="font-semibold text-gray-300">Logs</h4>
                    <pre className="bg-black/50 p-2 rounded text-xs text-red-300 overflow-x-auto max-h-48">
                        <code>{post.logs}</code>
                    </pre>
                </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
};

export default ForumPostDetailModal;
