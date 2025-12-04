export enum AppView {
  Dashboard = 'Dashboard',
  ForumPosts = 'Forum Posts',
  RAG = 'RAG Management',
  SlashCommands = 'Slash Commands',
  Playground = 'Playground',
  Settings = 'Settings',
}

export enum PostStatus {
  Unsolved = 'Unsolved',
  AIResponse = 'AI Response',
  HumanSupport = 'Human Support',
  HighPriority = 'High Priority',
  Solved = 'Solved',
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
  discordUrl?: string; // Direct link to Discord thread
}

export interface RagEntry {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  createdAt: string;
  createdBy: string;
}

export interface PendingRagEntry {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  createdAt: string;
  source: string; // "Auto-satisfaction" or "Staff via /mark_as_solved_with_review"
  threadId: string;
  conversationPreview: string;
}

export interface AutoResponse {
  id: string;
  name: string;
  triggerKeywords: string[];
  responseText: string;
  createdAt: string;
}

// fix(types): Add SlashCommand and CommandParameter types for the slash commands view.
export interface CommandParameter {
  name: string;
  description: string;
  type: 'string' | 'number' | 'boolean' | 'user' | 'channel' | 'role';
  required: boolean;
}

export interface SlashCommand {
  id: string;
  name: string;
  description: string;
  parameters: CommandParameter[];
  createdAt: string;
}

export interface BotSettings {
  systemPrompt: string;
  updatedAt: string;
}

export interface LeaderboardEntry {
  username: string;
  solved_count: number;
  avatar_url: string;
}

export interface Leaderboard {
  month: string; // Format: "2025-12"
  scores: Record<string, LeaderboardEntry>; // user_id -> entry
}