
import React, { useState, useMemo } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { Ticket, TicketStatus } from '../../types';
import StatusBadge from '../StatusBadge';
import TicketDetailModal from '../TicketDetailModal';

const TicketsView: React.FC = () => {
  const { tickets, setTickets } = useMockData();
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [filter, setFilter] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredTickets = useMemo(() => {
    return tickets
      .filter(ticket => {
        if (filter === 'All') return true;
        if (filter === 'In Progress') return [TicketStatus.AIResponse, TicketStatus.HumanSupport, TicketStatus.KeywordMatch].includes(ticket.status);
        return ticket.status === filter;
      })
      .filter(ticket => 
        ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ticket.user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ticket.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [tickets, filter, searchTerm]);

  const handleCloseModal = () => {
    setSelectedTicket(null);
  };
  
  const handleUpdateTicket = (updatedTicket: Ticket) => {
    setTickets(prevTickets => prevTickets.map(t => t.id === updatedTicket.id ? updatedTicket : t));
  };


  const filterOptions = ['All', 'In Progress', ...Object.values(TicketStatus)];

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
        <input
          type="text"
          placeholder="Search tickets..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full sm:w-1/2 bg-gray-700 text-white placeholder-gray-400 border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full sm:w-auto bg-gray-700 text-white border border-gray-600 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {filterOptions.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-700/50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ticket ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">User</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Title</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Priority</th>
            </tr>
          </thead>
          <tbody className="bg-gray-800 divide-y divide-gray-700">
            {filteredTickets.map((ticket) => (
              <tr key={ticket.id} onClick={() => setSelectedTicket(ticket)} className="hover:bg-gray-700/50 cursor-pointer">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{ticket.id}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <img className="h-10 w-10 rounded-full" src={ticket.user.avatar} alt="" />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-200">{ticket.user.name}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-200">{ticket.title}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={ticket.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <span className={`${ticket.priority === 'High' ? 'text-red-400' : ticket.priority === 'Medium' ? 'text-yellow-400' : 'text-green-400'}`}>{ticket.priority}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedTicket && <TicketDetailModal ticket={selectedTicket} onClose={handleCloseModal} onUpdate={handleUpdateTicket} />}
    </div>
  );
};

export default TicketsView;
   