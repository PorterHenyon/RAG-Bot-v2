import React, { useState, useMemo, useEffect } from 'react';
import { useMockData } from '../../hooks/useMockData';
import { ForumPost, PostStatus } from '../../types';
import PostStatusBadge from '../PostStatusBadge';
import ForumPostDetailModal from '../ForumPostDetailModal';
import { forumPostService } from '../../services/forumPostService';
import { dataService } from '../../services/dataService';

const ForumPostCard: React.FC<{ post: ForumPost; onClick: () => void }> = ({ post, onClick }) => {
  const handleDiscordLinkClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent opening the modal
    if (post.discordUrl) {
      window.open(post.discordUrl, '_blank');
    }
  };

  return (
    <div onClick={onClick} className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-5 border border-gray-700 hover:border-primary-500 cursor-pointer transition-all duration-300 hover:shadow-xl hover:scale-[1.02] group overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-r from-primary-500/0 to-primary-500/0 group-hover:from-primary-500/5 group-hover:to-primary-500/10 transition-all duration-300"></div>
      <div className="relative z-10">
        <div className="flex justify-between items-start">
          <h3 className="font-bold text-white mb-3 pr-4 text-lg group-hover:text-primary-300 transition-colors line-clamp-2">{post.postTitle}</h3>
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
          <img className="h-7 w-7 rounded-full ring-2 ring-gray-600 group-hover:ring-primary-500 transition-all" src={post.user.avatarUrl} alt={post.user.username} />
          <span className="text-sm text-gray-400 group-hover:text-gray-300 transition-colors">{post.user.username}</span>
        </div>
        <div className="flex flex-wrap gap-2 mb-3">
          {post.tags.map(tag => (
            <span key={tag} className="bg-gray-700/80 text-xs text-gray-300 font-semibold px-3 py-1 rounded-full border border-gray-600 group-hover:border-primary-500/50 transition-all">{tag}</span>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-4 text-right group-hover:text-gray-400 transition-colors">
          {new Date(post.createdAt).toLocaleString()}
        </p>
      </div>
    </div>
  );
};


const ForumPostsView: React.FC = () => {
  const { forumPosts, setForumPosts } = useMockData();
  const [selectedPost, setSelectedPost] = useState<ForumPost | null>(null);
  const [filter, setFilter] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [isPurging, setIsPurging] = useState<boolean>(false);
  const [showPurgeConfirm, setShowPurgeConfirm] = useState<boolean>(false);

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

  const handlePurgeForumPosts = async () => {
    try {
      setIsPurging(true);
      setShowPurgeConfirm(false);
      
      // Get ignored post IDs from bot settings
      let ignoredPostIds: string[] = [];
      try {
        const data = await dataService.fetchData();
        ignoredPostIds = data.botSettings?.ignored_post_ids || [];
      } catch (error) {
        console.error('Error fetching bot settings:', error);
      }

      // Purge posts (keep ignored ones)
      const result = await forumPostService.purgeForumPosts(ignoredPostIds);
      
      // Refresh forum posts
      const posts = await forumPostService.fetchForumPosts();
      setForumPosts(posts);
      
      // Show success message
      alert(`✅ Purge complete!\n\nDeleted: ${result.deleted}\nKept (main posts): ${result.kept}\nFailed: ${result.failed}`);
    } catch (error) {
      console.error('Error purging forum posts:', error);
      alert(`❌ Error purging forum posts: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsPurging(false);
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
    
    // Load immediately and refresh every 5 minutes (reduced from 30s to save bandwidth)
    // Only poll when tab is visible to save resources
    refreshForumPosts();
    const interval = setInterval(() => {
      if (isMounted && !document.hidden) {
        refreshForumPosts();
      }
    }, 300000); // 5 minutes instead of 30 seconds - saves 90% bandwidth
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const filterOptions = ['All', 'In Progress', ...Object.values(PostStatus)];

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-5 flex flex-col sm:flex-row justify-between items-center gap-4 border border-gray-700">
        <input
          type="text"
          placeholder="Search posts by title, user, tag..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full sm:w-1/2 bg-gray-700/50 text-white placeholder-gray-400 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all"
        />
        <div className="flex gap-3 w-full sm:w-auto">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="flex-1 sm:flex-none bg-gray-700/50 text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all cursor-pointer"
          >
            {filterOptions.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
          <button
            onClick={() => setShowPurgeConfirm(true)}
            disabled={isPurging || forumPosts.length === 0}
            className="px-4 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900 whitespace-nowrap"
            title="Delete all forum posts except main posts (ignored posts)"
          >
            {isPurging ? 'Purging...' : '🗑️ Purge Posts'}
          </button>
        </div>
      </div>

      {showPurgeConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-2xl p-6 border border-gray-700 max-w-md w-full">
            <h3 className="text-xl font-bold text-white mb-4">⚠️ Confirm Purge</h3>
            <p className="text-gray-300 mb-2">
              This will delete <strong className="text-red-400">{forumPosts.length}</strong> forum post{forumPosts.length !== 1 ? 's' : ''}.
            </p>
            <p className="text-gray-400 text-sm mb-6">
              Main posts (ignored posts) will be kept. This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={handlePurgeForumPosts}
                disabled={isPurging}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all"
              >
                {isPurging ? 'Purging...' : 'Yes, Purge All'}
              </button>
              <button
                onClick={() => setShowPurgeConfirm(false)}
                disabled={isPurging}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {filteredPosts.length === 0 ? (
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl shadow-lg p-12 text-center border border-gray-700">
          <div className="max-w-md mx-auto">
            <svg className="w-16 h-16 mx-auto text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="text-gray-300 text-xl font-semibold mb-2">Nothing here yet</p>
            <p className="text-gray-500 text-sm">
              Posts from Discord show up here once they're created.
            </p>
          </div>
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