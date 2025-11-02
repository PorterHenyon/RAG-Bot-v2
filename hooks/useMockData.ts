import { useState, useEffect } from 'react';
import { ForumPost, RagEntry, PostStatus, AutoResponse, Message, SlashCommand } from '../types';
import { dataService } from '../services/dataService';

// RAG entries initial data
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
        content: "If your settings reset every time you restart the macro, it's a file permissions issue. The macro needs to be able to write to its own folder. Navigate to your Revolution Macro installation folder, right-click it, select 'Properties', go to the 'Security' tab, and ensure your user account has 'Full control' permissions. Running the macro as an administrator can also solve this.",
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
        responseText: 'You can check for the latest version of the macro by clicking the "Check for Updates" button in the "About" tab. It\'s always a good idea to be on the latest version!',
        createdAt: '2024-10-30T11:00:00Z'
    }
];

const initialSlashCommands: SlashCommand[] = [
    {
      id: 'CMD-SYS-001',
      name: 'reload',
      description: 'Reloads the bot\'s configuration or command handlers. Requires Admin role.',
      parameters: [
        { name: 'module', description: 'The specific module to reload (e.g., "commands", "config").', type: 'string', required: false },
      ],
      createdAt: '2024-10-31T10:00:00Z',
    },
    {
      id: 'CMD-SYS-002',
      name: 'stop',
      description: 'Stops the bot process gracefully. Requires Admin role.',
      parameters: [],
      createdAt: '2024-10-31T10:05:00Z',
    },
];

export const useMockData = () => {
    // Start with empty array - API will populate if available
    const [forumPosts, setForumPosts] = useState<ForumPost[]>([]);
    const [ragEntries, setRagEntries] = useState<RagEntry[]>(initialRagEntries);
    const [autoResponses, setAutoResponses] = useState<AutoResponse[]>(initialAutoResponses);
    const [slashCommands, setSlashCommands] = useState<SlashCommand[]>(initialSlashCommands);

    // Load data from API on mount (only once, prevent flashing)
    useEffect(() => {
        let isMounted = true;
        let hasLoaded = false;
        const loadData = async () => {
            if (hasLoaded) return; // Prevent multiple loads
            try {
                const data = await dataService.fetchData();
                // Only update if component is still mounted
                if (isMounted) {
                    // Always use API data if available (even if empty) to clear defaults
                    // This ensures we show what's actually in Redis, not hardcoded defaults
                    if (data.ragEntries && Array.isArray(data.ragEntries)) {
                        setRagEntries(data.ragEntries);
                        if (data.ragEntries.length > 0) {
                            console.log(`✓ Loaded ${data.ragEntries.length} RAG entries from API`);
                        } else {
                            console.log(`✓ API returned empty RAG entries (database is empty)`);
                        }
                    }
                    if (data.autoResponses && Array.isArray(data.autoResponses)) {
                        setAutoResponses(data.autoResponses);
                        if (data.autoResponses.length > 0) {
                            console.log(`✓ Loaded ${data.autoResponses.length} auto-responses from API`);
                        } else {
                            console.log(`✓ API returned empty auto-responses (database is empty)`);
                        }
                    }
                    hasLoaded = true;
                }
            } catch (error) {
                console.error('Failed to load data from API, using local data:', error);
                hasLoaded = true; // Mark as loaded even on error to prevent retries
            }
        };
        loadData();
        return () => {
            isMounted = false;
        };
    }, []);

    // Load forum posts from API on mount and periodically
    useEffect(() => {
        let isMounted = true;
        const loadForumPosts = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL 
                    ? `${import.meta.env.VITE_API_URL}/api/forum-posts`
                    : `${window.location.origin}/api/forum-posts`;
                
                const response = await fetch(apiUrl);
                if (response.ok) {
                    const posts = await response.json();
                    // Always update with API data, even if empty array (clears mock data)
                    if (isMounted && posts && Array.isArray(posts)) {
                        setForumPosts(posts);
                        if (posts.length > 0) {
                            console.log(`✓ Loaded ${posts.length} forum post(s) from API`);
                        } else {
                            console.log(`✓ API returned empty array - cleared mock posts`);
                        }
                    }
                } else {
                    console.warn(`Failed to load forum posts: HTTP ${response.status}`);
                    // Clear posts if API fails (don't show mock data)
                    if (isMounted) {
                        setForumPosts([]);
                    }
                }
            } catch (error) {
                console.error('Failed to load forum posts from API:', error);
                // Clear posts if API fails (don't show mock data)
                if (isMounted) {
                    setForumPosts([]);
                }
            }
        };
        
        // Load immediately on mount
        loadForumPosts();
        // Refresh forum posts every 5 seconds for faster updates
        const interval = setInterval(() => {
            if (isMounted) {
                loadForumPosts();
            }
        }, 5000);
        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    // Sync data to API whenever RAG entries or auto-responses change (with debounce)
    useEffect(() => {
        // Skip sync on initial mount to prevent flashing
        let skipFirst = true;
        const timeoutId = setTimeout(() => {
            if (!skipFirst) {
                const syncData = async () => {
                    try {
                        await dataService.saveData(ragEntries, autoResponses);
                    } catch (error) {
                        console.error('Failed to sync data to API:', error);
                    }
                };
                syncData();
            }
            skipFirst = false;
        }, 2000); // Increased debounce to 2 seconds to reduce flashing
        return () => clearTimeout(timeoutId);
    }, [ragEntries, autoResponses]);

    useEffect(() => {
        const interval = setInterval(() => {
            setForumPosts(prevPosts => {
                const openPosts = prevPosts.filter(p => p.status !== PostStatus.Closed && p.status !== PostStatus.Solved);
                if (openPosts.length === 0) return prevPosts;
                
                const postToUpdate = openPosts[Math.floor(Math.random() * openPosts.length)];
                const newMessage: Message = {
                    author: 'User',
                    content: 'Any updates on this?? I\'m still stuck',
                    timestamp: new Date().toISOString()
                };

                return prevPosts.map(p => 
                    p.id === postToUpdate.id 
                        ? { ...p, conversation: [...p.conversation, newMessage] } 
                        : p
                );
            });
        }, 25000); // Add a new message every 25 seconds

        return () => clearInterval(interval);
    }, []);

    return { forumPosts, setForumPosts, ragEntries, setRagEntries, autoResponses, setAutoResponses, slashCommands, setSlashCommands };
};