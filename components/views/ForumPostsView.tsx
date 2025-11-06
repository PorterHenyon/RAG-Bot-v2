import React, { useState, useMemo, useEffect } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { ForumPost, PostStatus } from '../../types';
import PostStatusBadge from '../PostStatusBadge';
import ForumPostDetailModal from '../ForumPostDetailModal';
import { forumPostService } from '../../services/forumPostService';

const ForumPostCard: React.FC<{ post: ForumPost; onClick: () => void }> = ({ post, onClick }) => {
  return (
    <div onClick={onClick} className="bg-gray-800 rounded-lg shadow-lg p-4 border border-gray-700 hover:border-primary-500 cursor-pointer transition-all duration-200">
      <div className="flex justify-between items-start">
        <h3 className="font-bold text-white mb-2 pr-4">{post.postTitle}</h3>
        <PostStatusBadge status={post.status} />
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
      );
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
    
    // Load immediately and refresh every 5 seconds for faster updates
    refreshForumPosts();
    const interval = setInterval(() => {
      if (isMounted) {
        refreshForumPosts();
      }
    }, 5000);
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