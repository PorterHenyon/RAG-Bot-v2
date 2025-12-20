import React from 'react';
import { useMockData } from '../../hooks/useMockData';
import { PostStatus, ForumPost, Message } from '../../types';
import { ArrowRightIcon, DatabaseIcon, ChevronDownIcon } from '../icons';

const StatCard: React.FC<{ title: string; value: number; color: string }> = ({ title, value, color }) => (
  <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-6 rounded-xl shadow-lg border border-gray-700 hover:border-primary-500 transition-all duration-300 hover:shadow-xl hover:scale-105 group">
    <h3 className="text-gray-400 text-sm font-medium mb-2 group-hover:text-gray-300 transition-colors">{title}</h3>
    <p className={`text-4xl font-bold ${color} transition-transform group-hover:scale-110`}>{value}</p>
  </div>
);

const FlowStep: React.FC<{ title: string; description: string; children?: React.ReactNode }> = ({ title, description, children }) => (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-5 rounded-xl border border-gray-700 hover:border-primary-500 transition-all duration-300 shadow-lg hover:shadow-xl relative overflow-hidden group">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/0 to-primary-500/0 group-hover:from-primary-500/5 group-hover:to-primary-500/10 transition-all duration-300"></div>
        <div className="relative z-10">
            <h4 className="font-bold text-primary-400 text-lg mb-2">{title}</h4>
            <p className="text-sm text-gray-300 leading-relaxed">{description}</p>
            {children}
        </div>
    </div>
);

const FlowArrow: React.FC<{ label?: string }> = ({ label }) => (
  <div className="flex flex-col items-center my-2 mx-4 text-gray-500">
    {label && <span className="text-xs italic mb-1">{label}</span>}
    <ChevronDownIcon className="w-6 h-6" />
  </div>
);


const DashboardView: React.FC = () => {
  const { forumPosts } = useMockData();
  
  // Helper to check if a post was solved today
  const isSolvedToday = (post: ForumPost): boolean => {
    if (post.status !== PostStatus.Solved && post.status !== PostStatus.Closed) {
      return false;
    }
    
    // Check conversation messages for when it was marked as solved
    const solvedMessages = post.conversation.filter((msg: Message) => 
      msg.author === 'System' && 
      (msg.content.toLowerCase().includes('solved') || msg.content.toLowerCase().includes('closed'))
    );
    
    if (solvedMessages.length > 0) {
      // Use the most recent solved message timestamp
      const solvedTimestamp = new Date(solvedMessages[solvedMessages.length - 1].timestamp);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return solvedTimestamp >= today;
    }
    
    // Fallback: if no system message, check if status is Solved/Closed and created today
    // (less accurate but better than nothing)
    const createdAt = new Date(post.createdAt);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return createdAt >= today && (post.status === PostStatus.Solved || post.status === PostStatus.Closed);
  };
  
  const stats = {
    unsolved: forumPosts.filter((p: ForumPost) => p.status === PostStatus.Unsolved).length,
    inProgress: forumPosts.filter((p: ForumPost) => [PostStatus.AIResponse, PostStatus.HumanSupport, PostStatus.HighPriority].includes(p.status)).length,
    solvedToday: forumPosts.filter((p: ForumPost) => isSolvedToday(p)).length,
    // Total closed includes both Solved and Closed posts
    totalClosed: forumPosts.filter((p: ForumPost) => p.status === PostStatus.Closed || p.status === PostStatus.Solved).length
  };

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Unsolved Posts" value={stats.unsolved} color="text-blue-400" />
        <StatCard title="In Progress" value={stats.inProgress} color="text-purple-400" />
        <StatCard title="Solved Today" value={stats.solvedToday} color="text-green-400" />
        <StatCard title="Total Closed" value={stats.totalClosed} color="text-gray-400" />
      </div>

      <div>
        <h2 className="text-3xl font-bold mb-6 text-white">Support Workflow</h2>
        <div className="bg-gradient-to-br from-gray-800/60 to-gray-900/60 backdrop-blur-sm p-8 rounded-2xl shadow-2xl border border-gray-700/50">
            <div className="flex flex-col items-center text-center">
                 <FlowStep title="(Start) User Creates Forum Post" description="A user creates a new post in the designated support forum channel on Discord." />
                 <FlowArrow />
                 <FlowStep title="Auto-Response & Keyword Matching" description="Bot scans the new post for keywords to provide an instant, pre-written answer for common issues." />
                 <FlowArrow label="if unsolved" />
                 <FlowStep title="AI Response Generation (RAG)" description="Gemini uses the knowledge base to generate a detailed, context-aware answer to the user's post." />
                 <FlowArrow label="if unsolved" />
                 <FlowStep title="Human Support Escalation" description="The post is flagged for a human agent to step in and provide assistance directly in the forum thread." />
                 <FlowArrow />
                 <div className="flex items-center text-gray-400 mt-4">
                     <p className="mr-4">Human resolves the issue...</p>
                     <ArrowRightIcon className="w-6 h-6" />
                 </div>
                 <FlowArrow />
                 <FlowStep title="AI Summarizes Solution" description="After human resolution, Gemini analyzes the conversation and creates a concise summary of the fix." />
                  <FlowArrow />
                 <FlowStep title="Human Edits & Adds to Knowledge Base" description="An admin reviews the AI summary, refines it, and adds it to the RAG database for future use."/>
                 <div className="flex items-center text-gray-400 mt-4">
                     <ArrowRightIcon className="w-6 h-6 rotate-90" />
                     <DatabaseIcon className="w-12 h-12 mx-4" />
                     <span className="font-semibold">RAG Database Grows Smarter</span>
                 </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
