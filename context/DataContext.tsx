import React, { createContext, useState, ReactNode, Dispatch, SetStateAction } from 'react';
import { ForumPost, RagEntry, AutoResponse, PostStatus, Message } from '../types';

// --- INITIAL DATA (Same as the old useMockData hook) ---

const initialForumPosts: ForumPost[] = [
  {
    id: 'POST-001',
    user: { username: 'BeeKeeper#1234', id: '234567890123456789', avatarUrl: 'https://cdn.discordapp.com/avatars/234567890123456789/a_example.png' },
    postTitle: 'why is my charactor resetting instead of converting honey',
    status: PostStatus.New,
    tags: ['bug', 'scripting', 'honey'],
    createdAt: '2024-10-30T10:00:00Z',
    forumChannelId: '123456789',
    postId: '987654321098765432',
    conversation: [
      { author: 'User', content: 'my character keeps running back to the hive and resetting itslef when it should be converting my honey into pollen, i have bad english sry', timestamp: '2024-10-30T10:00:00Z' }
    ],
  },
  {
    id: 'POST-002',
    user: { username: 'Bob#5678', id: '345678901234567890', avatarUrl: 'https://cdn.discordapp.com/avatars/345678901234567890/b_example.png' },
    postTitle: 'How do I configure the new feature?',
    status: PostStatus.AIResponse,
    tags: ['question', 'feature'],
    createdAt: '2024-10-30T09:30:00Z',
    forumChannelId: '123456789',
    postId: '987654321098765433',
    conversation: [
        { author: 'User', content: 'I see the new "auto-sort" feature but I can\'t figure out how to turn it on.', timestamp: '2024-07-28T09:30:00Z' },
        { author: 'Bot', content: 'I can help with that! To enable "auto-sort", please navigate to Settings > Advanced and check the box labeled "Enable Auto-Sorting".', timestamp: '2024-07-28T09:31:00Z' }
    ],
  },
  {
    id: 'POST-003',
    user: { username: 'Charlie#9101', id: '456789012345678901', avatarUrl: 'https://cdn.discordapp.com/avatars/456789012345678901/c_example.png' },
    postTitle: 'Application crashes on startup',
    status: PostStatus.HumanSupport,
    tags: ['crash', 'urgent'],
    createdAt: '2024-10-29T15:00:00Z',
    forumChannelId: '123456789',
    postId: '987654321098765434',
    conversation: [
        { author: 'User', content: 'My application is crashing every time I open it. I tried reinstalling it but nothing works.', timestamp: '2024-07-27T15:00:00Z' },
        { author: 'Bot', content: 'I found some potential solutions, but they don\'t seem to match your issue perfectly. I am escalating this to a human support agent.', timestamp: '2024-07-27T15:02:00Z' },
        { author: 'Support', content: 'Hi Charlie, sorry you\'re running into this. Could you please provide your log files?', timestamp: '2024-07-27T16:00:00Z' },
    ],
    logs: 'Exception: NullReferenceException at Core.Startup.Initialize()...',
  },
];

const initialRagEntries: RagEntry[] = [
    {
        id: 'RAG-001',
        title: 'Character Resets Instead of Converting Honey',
        content: "This issue typically occurs when the 'Auto-Deposit' setting is enabled, but the main 'Gather' task is not set to pause during the conversion process. The macro incorrectly prioritizes gathering, causing it to reset the character's position and interrupt honey conversion. To fix this, go to Script Settings > Tasks > Gather and check the box 'Pause While Converting Honey'. Alternatively, you can disable 'Auto-Deposit' in the Hive settings.",
        keywords: ['honey', 'pollen', 'convert', 'reset', 'resets', 'resetting', 'gather', 'auto-deposit', 'stuck', 'hive'],
        createdAt: '2024-10-30T14:00:00Z',
        createdBy: 'System Knowledge',
    },
    {
        id: 'RAG-002',
        title: 'Error: "Failed to Initialize" on Startup',
        content: 'If Revolution Macro shows a "failed to initialize" error, it usually means the configuration file is corrupt. To fix this, close the macro, navigate to its installation directory, find the `config.json` file, and delete it. When you restart the macro, it will generate a fresh, default config file, resolving the issue.',
        keywords: ['initialize', 'error', 'update', 'fix', 'config.json', 'startup', 'starting up', 'launch'],
        createdAt: '2024-10-29T14:00:00Z',
        createdBy: 'System Knowledge',
    },
    {
        id: 'RAG-003',
        title: 'License Key Error: "Invalid Key" or "Activation Limit Reached"',
        content: "If you get an 'Invalid Key' error, please double-check that you have copied the entire key from your purchase email without any extra spaces. If the error is 'Activation Limit Reached', it means your key is already active on another machine. You must first deactivate it from the old machine using the 'Deactivate License' button in the macro's 'About' tab, or log into your account on the revolutionmacro.com website to manage your active machines.",
        keywords: ['license', 'key', 'activation', 'invalid', 'limit', 'hwid', 'deactivate', 'buy'],
        createdAt: '2024-10-28T11:00:00Z',
        createdBy: 'System Knowledge',
    },
    {
        id: 'RAG-004',
        title: 'Antivirus or Firewall is Blocking the Macro',
        content: "Antivirus software can sometimes incorrectly flag Revolution Macro as a threat due to its nature of controlling mouse and keyboard inputs. This is a false positive. To resolve this, you must add an exception or exclusion in your antivirus settings for the entire Revolution Macro installation folder, not just the .exe file. This will prevent the antivirus from quarantining or deleting critical files.",
        keywords: ['antivirus', 'virus', 'trojan', 'firewall', 'blocked', 'defender', 'avast', 'norton', 'false positive'],
        createdAt: '2024-10-27T18:00:00Z',
        createdBy: 'System Knowledge',
    },
    {
        id: 'RAG-005',
        title: 'Character is Stuck, Running into Walls, or Not Moving',
        content: "If your character gets stuck, it's almost always a pathing issue. First, try using the 'Unstuck' button on the main UI. If the problem persists, go to the 'Pathing' tab and click 'Recalculate Navigation Mesh' for your current map. Also, ensure your character's speed setting in the macro matches its in-game speed to avoid desync issues.",
        keywords: ['stuck', 'moving', 'wall', 'loop', 'pathing', 'navmesh', 'navigation'],
        createdAt: '2024-10-26T15:20:00Z',
        createdBy: 'System Knowledge',
    },
    {
        id: 'RAG-006',
        title: 'Macro Cannot Find the Game Window',
        content: "For the macro to correctly hook into the game, the game must be running in either 'Windowed' or 'Borderless Windowed' mode. Fullscreen mode is not supported. Additionally, try running Revolution Macro as an Administrator by right-clicking the icon and selecting 'Run as Administrator'. This gives it the necessary permissions to interact with other application windows.",
        keywords: ['find game', 'detect', 'attach', 'hook', 'windowed', 'fullscreen', 'admin', 'administrator'],
        createdAt: '2024-10-25T09:00:00Z',
        createdBy: 'System Knowledge',
    },
    {
        id: 'RAG-007',
        title: 'How to Configure "Smart Gather"',
        content: "The 'Smart Gather' feature allows you to prioritize resources. In the 'Gather' tab, you can create a priority list. Add the names of the items you want to collect (e.g., 'Sunflower', 'Blue Flower') and order them from highest to lowest priority. You can also add items to an 'Ignore List' to ensure the macro never collects them.",
        keywords: ['smart gather', 'priority', 'ignore list', 'filter', 'resources', 'items', 'collect'],
        createdAt: '2024-10-24T13:00:00Z',
        createdBy: 'System Knowledge',
    },
    {
        id: 'RAG-008',
        title: 'Script Settings Not Saving After Restart',
        content: `If your settings reset every time you restart the macro, it's a file permissions issue. The macro needs to be able to write to its own folder. Navigate to your Revolution Macro installation folder, right-click it, select 'Properties', go to the 'Security' tab, and ensure your user account has 'Full control' permissions. Running the macro as an administrator can also solve this.`,
        keywords: ['saving', 'settings', 'reset', 'restart', 'config', 'permissions', 'read-only'],
        createdAt: '2024-10-23T10:45:00Z',
        createdBy: 'System Knowledge',
    }
];

const initialAutoResponses: AutoResponse[] = [
    {
        id: 'AR-001',
        name: 'Password Reset',
        triggerKeywords: ['password', 'reset', 'forgot', 'lost account'],
        responseText: 'You can reset your password by visiting this link: [https://revolutionmacro.com/password-reset](https://revolutionmacro.com/password-reset).',
        createdAt: '2024-07-28T12:00:00Z'
    },
    {
        id: 'AR-002',
        name: 'Check Server Status',
        triggerKeywords: ['down', 'offline', 'server status', 'connection issue'],
        responseText: 'It seems you might be having a connection issue. You can check our server status in real-time on our status page: [https://status.revolutionmacro.com](https://status.revolutionmacro.com).',
        createdAt: '2024-07-28T12:05:00Z'
    },
    {
        id: 'AR-003',
        name: 'Check for Updates',
        triggerKeywords: ['update', 'new version', 'latest'],
        responseText: `You can check for the latest version of the macro by clicking the "Check for Updates" button in the "About" tab. It's always a good idea to be on the latest version!`,
        createdAt: '2024-10-30T11:00:00Z'
    }
];

// --- CONTEXT DEFINITION ---

interface IDataContext {
    forumPosts: ForumPost[];
    setForumPosts: Dispatch<SetStateAction<ForumPost[]>>;
    ragEntries: RagEntry[];
    setRagEntries: Dispatch<SetStateAction<RagEntry[]>>;
    autoResponses: AutoResponse[];
    setAutoResponses: Dispatch<SetStateAction<AutoResponse[]>>;
}

export const DataContext = createContext<IDataContext>({} as IDataContext);

export const DataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [forumPosts, setForumPosts] = useState<ForumPost[]>(initialForumPosts);
    const [ragEntries, setRagEntries] = = useState<RagEntry[]>(initialRagEntries);
    const [autoResponses, setAutoResponses] = useState<AutoResponse[]>(initialAutoResponses);

    return (
        <DataContext.Provider value={{
            forumPosts, setForumPosts,
            ragEntries, setRagEntries,
            autoResponses, setAutoResponses
        }}>
            {children}
        </DataContext.Provider>
    );
};
