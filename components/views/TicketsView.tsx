
import React, { useState, useMemo } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { ForumPost, PostStatus } from '../../types';
import StatusBadge from '../StatusBadge';
import TicketDetailModal from '../TicketDetailModal';

// refactor(terminology): Replaced "Ticket" with "Post" in variables and UI to align with forum context.
const TicketsView: React.FC = () => {
  const { forumPosts, setForumPosts } = useMockData();
  const [selectedPost, setSelectedPost] = useState<ForumPost | null>(null);
  const [filter, setFilter] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredPosts = useMemo(() => {
    return forumPosts
      .filter(post => {
        if (filter === 'All') return true;
        if (filter === 'In Progress') return [PostStatus.AIResponse, PostStatus.HumanSupport].includes(post.status);
        return post.status === filter;
      })
      .filter(post => 
        post.postTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
        post.user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        post.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [forumPosts, filter, searchTerm]);

  const handleCloseModal = () => {
    setSelectedPost(null);
  };
  
  const handleUpdatePost = (updatedPost: ForumPost) => {
    setForumPosts(prevPosts => prevPosts.map(p => p.id === updatedPost.id ? updatedPost : p));
  };


  const filterOptions = ['All', 'In Progress', ...Object.values(PostStatus)];

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
        <input
          type="text"
          placeholder="Search posts..."
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
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Post ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">User</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Title</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-gray-800 divide-y divide-gray-700">
            {filteredPosts.map((post) => (
              <tr key={post.id} onClick={() => setSelectedPost(post)} className="hover:bg-gray-700/50 cursor-pointer">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">{post.id}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <img className="h-10 w-10 rounded-full" src={post.user.avatarUrl} alt="" />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-200">{post.user.username}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-200">{post.postTitle}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={post.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* refactor(props): Pass selectedPost to the 'post' prop of the modal. */}
      {selectedPost && <TicketDetailModal post={selectedPost} onClose={handleCloseModal} onUpdate={handleUpdatePost} />}
    </div>
  );
};

export default TicketsView;