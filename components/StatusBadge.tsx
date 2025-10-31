
import React from 'react';
import { TicketStatus } from '../types';

interface StatusBadgeProps {
  status: TicketStatus;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
  const statusStyles: Record<TicketStatus, string> = {
    [TicketStatus.New]: 'bg-blue-500 text-blue-100',
    [TicketStatus.KeywordMatch]: 'bg-indigo-500 text-indigo-100',
    [TicketStatus.AIResponse]: 'bg-purple-500 text-purple-100',
    [TicketStatus.HumanSupport]: 'bg-yellow-500 text-yellow-100',
    [TicketStatus.Resolved]: 'bg-green-500 text-green-100',
    [TicketStatus.Escalated]: 'bg-red-500 text-red-100',
    [TicketStatus.Closed]: 'bg-gray-600 text-gray-100',
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-semibold rounded-full ${statusStyles[status] || 'bg-gray-500 text-gray-100'}`}
    >
      {status}
    </span>
  );
};

export default StatusBadge;
   