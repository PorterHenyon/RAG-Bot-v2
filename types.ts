export enum AppView {
  Dashboard = 'Dashboard',
  ForumPosts = 'Forum Posts',
  RAG = 'RAG Management',
  Playground = 'Playground',
  Settings = 'Settings',
}

export enum PostStatus {
  New = 'New',
  AIResponse = 'AI Response',
  HumanSupport = 'Human Support',
  Resolved = 'Resolved',
  Closed = 'Closed',
}

export interface Message {
  author: 'User' | 'Bot' | 'Support' | 'System';
  content: string;
  timestamp: string;
}

export interface ForumPost {
  id: string;
  user: {
    username: string;
    id: string;
    avatarUrl: string;
  };
  postTitle: string;
  status: PostStatus;
  tags: string[];
  createdAt: string;
  forumChannelId: string;
  postId: string;
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

export interface AutoResponse {
  id: string;
  name: string;
  triggerKeywords: string[];
  responseText: string;
  createdAt: string;
}
