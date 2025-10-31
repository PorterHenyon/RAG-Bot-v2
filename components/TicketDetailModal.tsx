
import React, { useState } from 'react';
import { Ticket, Message, TicketStatus } from '../types';
import { XMarkIcon, UserIcon, BotIcon, SupportIcon } from './icons';
import StatusBadge from './StatusBadge';
import { geminiService } from '../../services/geminiService';

interface TicketDetailModalProps {
  ticket: Ticket;
  onClose: () => void;
  onUpdate: (ticket: Ticket) => void;
}

const MessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.author === 'User';
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

const TicketDetailModal: React.FC<TicketDetailModalProps> = ({ ticket, onClose, onUpdate }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingAction, setProcessingAction] = useState<string | null>(null);

  const handleRequestLogs = () => {
    setIsProcessing(true);
    setProcessingAction('Requesting Logs');
    setTimeout(() => {
        const botMessage: Message = { author: 'Bot', content: 'I have sent a DM to the user with a code to upload their logs.', timestamp: new Date().toISOString()};
        const updatedTicket = { ...ticket, conversation: [...ticket.conversation, botMessage]};
        onUpdate(updatedTicket);

        setTimeout(() => {
            const botMessage2: Message = { author: 'Bot', content: 'Logs have been received.', timestamp: new Date().toISOString()};
            const updatedTicket2 = { ...updatedTicket, conversation: [...updatedTicket.conversation, botMessage2], logs: 'DEBUG: User authenticated. INFO: Initializing modules... ERROR: Module "SuperRender" failed to load. Dependency "TurboCore" not found.'};
            onUpdate(updatedTicket2);
            setIsProcessing(false);
            setProcessingAction(null);
        }, 3000);
    }, 1000);
  };

  const handleSummarize = async () => {
    if (ticket.status !== TicketStatus.Resolved) {
        alert("Can only summarize resolved tickets.");
        return;
    }
    setIsProcessing(true);
    setProcessingAction('Summarizing');
    const summary = await geminiService.summarizeConversation(ticket.conversation);
    const summaryMessage: Message = { author: 'Bot', content: `AI Summary: ${summary}`, timestamp: new Date().toISOString()};
    onUpdate({...ticket, conversation: [...ticket.conversation, summaryMessage]});
    setIsProcessing(false);
    setProcessingAction(null);
    // Here you would typically open another modal to confirm adding this to RAG
    alert('Summary generated and added to conversation history. Next, you would add this to the RAG database.');
  };
  
  const handleEscalate = () => {
      onUpdate({...ticket, status: TicketStatus.Escalated});
      onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-2xl w-full max-w-4xl h-[90vh] flex flex-col">
        <header className="flex items-center justify-between p-4 border-b border-gray-700 flex-shrink-0">
          <div>
            <h2 className="text-xl font-bold text-white">{ticket.title}</h2>
            <p className="text-sm text-gray-400">
              <span className="font-semibold">{ticket.id}</span> from {ticket.user.name}
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-700">
            <XMarkIcon className="w-6 h-6 text-gray-300" />
          </button>
        </header>

        <div className="flex-1 flex overflow-hidden">
          {/* Main Content */}
          <main className="flex-1 p-4 overflow-y-auto">
            <h3 className="text-lg font-semibold text-white mb-2">Conversation</h3>
            <div className="flex flex-col">
              {ticket.conversation.map((msg, index) => <MessageBubble key={index} message={msg} />)}
            </div>
          </main>

          {/* Sidebar */}
          <aside className="w-80 bg-gray-800/50 border-l border-gray-700 p-4 flex-shrink-0 flex flex-col gap-4 overflow-y-auto">
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-300">Status</h4>
              <StatusBadge status={ticket.status} />
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-300">Priority</h4>
              <p className={`font-bold ${ticket.priority === 'High' ? 'text-red-400' : ticket.priority === 'Medium' ? 'text-yellow-400' : 'text-green-400'}`}>{ticket.priority}</p>
            </div>
             <div className="space-y-2">
              <h4 className="font-semibold text-gray-300">Classification</h4>
              <p className="text-gray-200">{ticket.type}</p>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-semibold text-gray-300">Actions</h4>
              <div className="flex flex-col gap-2">
                <button 
                    onClick={handleRequestLogs} 
                    disabled={isProcessing || !!ticket.logs}
                    className="w-full text-left bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded disabled:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                    {isProcessing && processingAction === 'Requesting Logs' ? 'Requesting...' : ticket.logs ? 'Logs Received' : 'Request Logs'}
                </button>
                <button 
                    onClick={handleSummarize}
                    disabled={isProcessing || ticket.status !== TicketStatus.Resolved}
                    className="w-full text-left bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded disabled:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                    {isProcessing && processingAction === 'Summarizing' ? 'Summarizing...' : 'Summarize & Add to RAG'}
                </button>
                <button 
                    onClick={handleEscalate}
                    disabled={isProcessing || ticket.status === TicketStatus.Escalated}
                    className="w-full text-left bg-red-600 hover:bg-red-500 text-white font-bold py-2 px-4 rounded disabled:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                    Escalate to Devs
                </button>
              </div>
            </div>

            {ticket.logs && (
                <div className="space-y-2">
                    <h4 className="font-semibold text-gray-300">Logs</h4>
                    <pre className="bg-black/50 p-2 rounded text-xs text-red-300 overflow-x-auto max-h-48">
                        <code>{ticket.logs}</code>
                    </pre>
                </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
};

export default TicketDetailModal;
   