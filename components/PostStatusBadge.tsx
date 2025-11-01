import React from 'react';
import { PostStatus } from '../types';

interface PostStatusBadgeProps {
  status: PostStatus;
}

const PostStatusBadge: React.FC<PostStatusBadgeProps> = ({ status }) => {
  const statusStyles: Record<PostStatus, string> = {
    [PostStatus.Unsolved]: 'bg-blue-500 text-blue-100',
    [PostStatus.AIResponse]: 'bg-purple-500 text-purple-100',
    [PostStatus.HumanSupport]: 'bg-yellow-500 text-yellow-100',
    [PostStatus.Solved]: 'bg-green-500 text-green-100',
    [PostStatus.Closed]: 'bg-gray-600 text-gray-100',
  };

  return (
    <span
      className={`px-2 py-1 text-xs font-semibold rounded-full ${statusStyles[status] || 'bg-gray-500 text-gray-100'}`}
    >
      {status}
    </span>
  );
};

export default PostStatusBadge;
