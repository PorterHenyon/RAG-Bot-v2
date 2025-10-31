
export enum AppView {
  Dashboard = 'Dashboard',
  Tickets = 'Tickets',
  RAG = 'RAG Management',
  Settings = 'Settings',
}

export enum TicketStatus {
  New = 'New',
  KeywordMatch = 'Keyword Match',
  AIResponse = 'AI Response',
  HumanSupport = 'Human Support',
  Resolved = 'Resolved',
  Escalated = 'Escalated',
  Closed = 'Closed',
}

export interface Message {
  author: 'User' | 'Bot' | 'Support';
  content: string;
  timestamp: string;
}

export interface Ticket {
  id: string;
  user: {
    name: string;
    avatar: string;
  };
  title: string;
  status: TicketStatus;
  priority: 'Low' | 'Medium' | 'High';
  type: 'User Error' | 'Macro Issue' | 'Unclassified';
  createdAt: string;
  conversation: Message[];
  logs?: string;
}

export interface RagEntry {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  createdAt: string;
  createdBy: string;
}
   