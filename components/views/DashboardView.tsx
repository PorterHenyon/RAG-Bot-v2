
import React from 'react';
import { useMockData } from '../../hooks/useMockData';
import { TicketStatus } from '../../types';
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
  const { tickets } = useMockData();
  const stats = {
    new: tickets.filter(t => t.status === TicketStatus.New).length,
    inProgress: tickets.filter(t => [TicketStatus.AIResponse, TicketStatus.HumanSupport, TicketStatus.KeywordMatch].includes(t.status)).length,
    escalated: tickets.filter(t => t.status === TicketStatus.Escalated).length,
    resolved: tickets.filter(t => t.status === TicketStatus.Resolved).length,
  };

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="New Tickets" value={stats.new} color="text-blue-400" />
        <StatCard title="In Progress" value={stats.inProgress} color="text-purple-400" />
        <StatCard title="Escalated" value={stats.escalated} color="text-red-400" />
        <StatCard title="Resolved Today" value={stats.resolved} color="text-green-400" />
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4 text-white">Support Workflow</h2>
        <div className="bg-gray-800/50 p-6 rounded-lg shadow-inner">
            <div className="flex flex-col items-center">
                 <FlowStep title="(Start) Support Needed" description="A new support request is created by a user." />
                 <FlowArrow />
                 <FlowStep title="Common Issue/Keyword Matching" description="Bot scans for keywords to match with existing manual solutions." />
                 
                 <div className="w-full flex justify-center items-start my-4">
                    <div className="flex flex-col items-center w-1/3">
                        <FlowArrow label="if solved"/>
                        <FlowStep title="Close Ticket" description="The issue is resolved."/>
                    </div>
                    <div className="flex flex-col items-center w-1/3 mt-6">
                       <p className="text-sm italic text-gray-400 mb-1">unsolved</p>
                       <ArrowRightIcon className="w-6 h-6 text-gray-500"/>
                    </div>
                    <div className="flex flex-col items-center w-1/3">
                        <div className="flex items-center text-gray-400">
                            <DatabaseIcon className="w-10 h-10 mr-2" />
                            <span>Well-made Guides & Fixes</span>
                        </div>
                    </div>
                 </div>

                 <FlowStep title="Use AI Response" description="Gemini generates a response using the RAG database of guides and fixes." />
                 <FlowArrow />
                
                 <div className="w-full flex justify-center items-start my-4">
                    <div className="flex flex-col items-center w-1/3">
                        <FlowArrow label="if solved"/>
                        <FlowStep title="Close Ticket" description="The issue is resolved."/>
                    </div>
                    <div className="flex flex-col items-center w-1/3 px-4">
                        <FlowArrow label="unsolved"/>
                        <FlowStep title="Human Support" description="Ticket is escalated to a human agent. *Doesn't include dev responses for macro bugs."/>
                        <FlowArrow />
                        <FlowStep title="AI Analyze Solution" description="After human resolution, Gemini analyzes and summarizes the solution."/>
                        <FlowArrow />
                        <FlowStep title="Human Editor & Indexer" description="A human confirms the AI summary and adds it to the RAG database."/>
                    </div>
                     <div className="flex flex-col items-center w-1/3">
                       <FlowArrow label="if still unsolved"/>
                       <FlowStep title="Escalate" description="Tell Liam or escalate to developers."/>
                    </div>
                 </div>

                 <div className="flex items-center text-gray-400 mt-4">
                     <ArrowRightIcon className="w-6 h-6 rotate-90" />
                     <DatabaseIcon className="w-12 h-12 mx-4" />
                     <span className="font-semibold">RAG Database</span>
                 </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
   