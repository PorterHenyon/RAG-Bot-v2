
import { useState } from 'react';
import { Ticket, RagEntry, TicketStatus } from '../types';

const initialTickets: Ticket[] = [
  {
    id: 'TKT-001',
    user: { name: 'Alice', avatar: 'https://i.pravatar.cc/150?u=alice' },
    title: 'Macro not loading after update',
    status: TicketStatus.New,
    priority: 'High',
    type: 'Unclassified',
    createdAt: '2024-07-28T10:00:00Z',
    conversation: [
      { author: 'User', content: 'My macro is not loading after the recent update. I get a "failed to initialize" error.', timestamp: '2024-07-28T10:00:00Z' }
    ],
  },
  {
    id: 'TKT-002',
    user: { name: 'Bob', avatar: 'https://i.pravatar.cc/150?u=bob' },
    title: 'How do I configure the new feature?',
    status: TicketStatus.AIResponse,
    priority: 'Low',
    type: 'User Error',
    createdAt: '2024-07-28T09:30:00Z',
    conversation: [
        { author: 'User', content: 'I see the new "auto-sort" feature but I can\'t figure out how to turn it on.', timestamp: '2024-07-28T09:30:00Z' },
        { author: 'Bot', content: 'I can help with that! To enable "auto-sort", please navigate to Settings > Advanced and check the box labeled "Enable Auto-Sorting".', timestamp: '2024-07-28T09:31:00Z' }
    ],
  },
  {
    id: 'TKT-003',
    user: { name: 'Charlie', avatar: 'https://i.pravatar.cc/150?u=charlie' },
    title: 'Application crashes on startup',
    status: TicketStatus.HumanSupport,
    priority: 'High',
    type: 'Macro Issue',
    createdAt: '2024-07-27T15:00:00Z',
    conversation: [
        { author: 'User', content: 'My application is crashing every time I open it. I tried reinstalling it but nothing works.', timestamp: '2024-07-27T15:00:00Z' },
        { author: 'Bot', content: 'I found some potential solutions, but they don\'t seem to match your issue perfectly. I am escalating this to a human support agent.', timestamp: '2024-07-27T15:02:00Z' },
        { author: 'Support', content: 'Hi Charlie, sorry you\'re running into this. Could you please provide your log files?', timestamp: '2024-07-27T16:00:00Z' },
    ],
    logs: 'Exception: NullReferenceException at Core.Startup.Initialize()...',
  },
  {
    id: 'TKT-004',
    user: { name: 'Diana', avatar: 'https://i.pravatar.cc/150?u=diana' },
    title: 'Payment issue',
    status: TicketStatus.Resolved,
    priority: 'Medium',
    type: 'User Error',
    createdAt: '2024-07-26T11:00:00Z',
    conversation: [
        { author: 'User', content: 'My payment was declined but my card is fine.', timestamp: '2024-07-26T11:00:00Z' },
        { author: 'Support', content: 'It seems there was a temporary issue with our payment processor. I have manually processed your payment. Everything should be working now.', timestamp: '2024-07-26T11:15:00Z' },
        { author: 'User', content: 'It works! Thank you!', timestamp: '2024-07-26T11:16:00Z' },
    ],
  },
    {
    id: 'TKT-005',
    user: { name: 'Eve', avatar: 'https://i.pravatar.cc/150?u=eve' },
    title: 'Critical bug in production',
    status: TicketStatus.Escalated,
    priority: 'High',
    type: 'Macro Issue',
    createdAt: '2024-07-28T11:00:00Z',
    conversation: [
        { author: 'User', content: 'The main feature is broken and causing data loss for my team!', timestamp: '2024-07-28T11:00:00Z' },
        { author: 'Support', content: 'This is a critical issue. I have escalated it directly to the lead developer. We are investigating now.', timestamp: '2024-07-28T11:05:00Z' },
    ],
    logs: 'FATAL: DataCorruptionException at Services.Data.Save()...',
  },
];

const initialRagEntries: RagEntry[] = [
    {
        id: 'RAG-001',
        title: 'Fix for "Failed to Initialize" Error on Update',
        content: 'If the macro shows a "failed to initialize" error after an update, the user should delete the `config.json` file from the installation directory and restart the application. This will regenerate a default config file and resolve the issue.',
        keywords: ['initialize', 'error', 'update', 'fix', 'config.json'],
        createdAt: '2024-07-25T14:00:00Z',
        createdBy: 'Liam',
    },
    {
        id: 'RAG-002',
        title: 'Enabling Beta Features',
        content: 'To enable beta features, go to Settings > About and click the version number 7 times. A new "Developer" tab will appear where beta features can be toggled.',
        keywords: ['beta', 'features', 'developer', 'enable', 'hidden'],
        createdAt: '2024-07-24T18:00:00Z',
        createdBy: 'Support Team',
    }
];

export const useMockData = () => {
    const [tickets, setTickets] = useState<Ticket[]>(initialTickets);
    const [ragEntries, setRagEntries] = useState<RagEntry[]>(initialRagEntries);

    return { tickets, setTickets, ragEntries, setRagEntries };
};
   