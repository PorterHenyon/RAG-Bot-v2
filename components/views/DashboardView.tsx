import React, { useContext } from 'react';
import { DataContext } from '../../context/DataContext';
import { PostStatus } from '../../types';
import { ArrowRightIcon, DatabaseIcon, ChevronDownIcon } from '../icons';

const StatCard: React.FC<{ title: string; value: number; color: string }> = ({ title, value, color }) => (
  <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
    <h3 className="text-gray-400 text-sm font-medium">{title}</h3>
    <p className={`text-3xl font-bold ${color}`}>{value}</p>
  </div>
);

const FlowStep: React.FC<{ title: string; description: string; children?: React.ReactNode }> = ({ title, description, children }) => (
    <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 relative">
        <h4 className="font-bold text-primary-400">{title}</h4>
        <p className="text-sm text-gray-300 mt-1">{description}</p>
        {children}
    </div>
);

const FlowArrow: React.FC<{ label?: string }> = ({ label }) => (
  <div className="flex flex-col items-center my-2 mx-4 text-gray-500">
    {label && <span className="text-xs italic mb-1">{label}</span>}
    <ChevronDownIcon className="w-6 h-6" />
  </div>
);


const DashboardView: React.FC = () => {
  const { forumPosts } = useContext(DataContext);
  const stats = {
    new: forumPosts.filter(p => p.status === PostStatus.New).length,
    inProgress: forumPosts.filter(p => [PostStatus.AIResponse, PostStatus.HumanSupport].includes(p.status)).length,
    resolved: forumPosts.filter(p => p.status === PostStatus.Resolved).length,
    closed: forumPosts.filter(p => p.status === PostStatus.Closed).length
  };

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="New Posts" value={stats.new} color="text-blue-400" />
        <StatCard title="In Progress" value={stats.inProgress} color="text-purple-400" />
        <StatCard title="Resolved Today" value={stats.resolved} color="text-green-400" />
        <StatCard title="Total Closed" value={stats.closed} color="text-gray-400" />
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4 text-white">Support Workflow</h2>
        <div className="bg-gray-800/50 p-6 rounded-lg shadow-inner">
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
