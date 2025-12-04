import React, { useState, useMemo, useEffect } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { ForumPost, PostStatus } from '../../types';
import PostStatusBadge from '../PostStatusBadge';
import ForumPostDetailModal from '../ForumPostDetailModal';
import { forumPostService } from '../../services/forumPostService';

const ForumPostCard: React.FC<{ post: ForumPost; onClick: () => void }> = ({ post, onClick }) => {
  const handleDiscordLinkClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent opening the modal
    if (post.discordUrl) {
      window.open(post.discordUrl, '_blank');
    }
  };

  return (
    <div onClick={onClick} className="bg-gray-800 rounded-lg shadow-lg p-4 border border-gray-700 hover:border-primary-500 cursor-pointer transition-all duration-200">
      <div className="flex justify-between items-start">
        <h3 className="font-bold text-white mb-2 pr-4">{post.postTitle}</h3>
        <div className="flex items-center gap-2">
          {post.discordUrl && (
            <button
              onClick={handleDiscordLinkClick}
              className="text-gray-400 hover:text-blue-400 transition-colors p-1"
              title="Open in Discord"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
              </svg>
            </button>
          )}
          <PostStatusBadge status={post.status} />
        </div>
      </div>
      <div className="flex items-center gap-2 mb-3">
        <img className="h-6 w-6 rounded-full" src={post.user.avatarUrl} alt={post.user.username} />
        <span className="text-sm text-gray-400">{post.user.username}</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {post.tags.map(tag => (
          <span key={tag} className="bg-gray-700 text-xs text-gray-300 font-semibold px-2 py-1 rounded-full">{tag}</span>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-3 text-right">
        {new Date(post.createdAt).toLocaleString()}
      </p>
    </div>
  );
};


const ForumPostsView: React.FC = () => {
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
        post.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        post.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      )
      .sort((a, b) => {
        // High priority posts always come first
        if (a.status === PostStatus.HighPriority && b.status !== PostStatus.HighPriority) return -1;
        if (a.status !== PostStatus.HighPriority && b.status === PostStatus.HighPriority) return 1;
        // Otherwise, sort by creation date (newest first)
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });
  }, [forumPosts, filter, searchTerm]);

  const handleCloseModal = () => {
    setSelectedPost(null);
  };
  
  const handleUpdatePost = async (updatedPost: ForumPost) => {
    try {
      await forumPostService.updateForumPost(updatedPost);
      setForumPosts(prevPosts => prevPosts.map(p => p.id === updatedPost.id ? updatedPost : p));
    } catch (error) {
      console.error('Error updating post:', error);
      // Still update locally even if API fails
      setForumPosts(prevPosts => prevPosts.map(p => p.id === updatedPost.id ? updatedPost : p));
    }
  };

  const handleDeletePost = async (postId: string): Promise<void> => {
    try {
      await forumPostService.deleteForumPost(postId);
      setForumPosts(prevPosts => prevPosts.filter(p => p.id !== postId));
      if (selectedPost?.id === postId) {
        setSelectedPost(null);
      }
    } catch (error) {
      console.error('Error deleting post:', error);
      // Still delete locally even if API fails
      setForumPosts(prevPosts => prevPosts.filter(p => p.id !== postId));
      if (selectedPost?.id === postId) {
        setSelectedPost(null);
      }
      // Re-throw so modal can handle it
      throw error;
    }
  };

  // Periodically refresh forum posts from API
  useEffect(() => {
    let isMounted = true;
    const refreshForumPosts = async () => {
      try {
        const posts = await forumPostService.fetchForumPosts();
        // Always update with API data, even if empty array (clears mock data)
        if (isMounted && posts && Array.isArray(posts)) {
          setForumPosts(posts);
        }
      } catch (error) {
        console.error('Error refreshing forum posts:', error);
      }
    };
    
    // Load immediately and refresh every 30 seconds (reduced from 5s to save bandwidth)
    // Only poll when tab is visible to save resources
    refreshForumPosts();
    const interval = setInterval(() => {
      if (isMounted && !document.hidden) {
        refreshForumPosts();
      }
    }, 30000); // 30 seconds instead of 5
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const filterOptions = ['All', 'In Progress', ...Object.values(PostStatus)];

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg shadow-lg p-4 flex flex-col sm:flex-row justify-between items-center gap-4">
        <input
          type="text"
          placeholder="Search posts by title, user, tag..."
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

      {filteredPosts.length === 0 ? (
        <div className="bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          <p className="text-gray-400 text-lg">Nothing here yet</p>
          <p className="text-gray-500 text-sm mt-2">
            Posts from Discord show up here once they're created.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredPosts.map((post) => (
            <ForumPostCard key={post.id} post={post} onClick={() => setSelectedPost(post)} />
          ))}
        </div>
      )}

      {selectedPost && <ForumPostDetailModal post={selectedPost} onClose={handleCloseModal} onUpdate={handleUpdatePost} onDelete={handleDeletePost} />}
    </div>
  );
};

export default ForumPostsView;