import { useState, useEffect } from 'react';
import { ForumPost, RagEntry, PostStatus, AutoResponse, Message, SlashCommand, BotSettings } from '../types';
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
    {
      id: 'CMD-SYS-003',
      name: 'ask',
      description: 'Ask the bot a question using the RAG knowledge base. Staff can use this to quickly find answers. Requires Admin role.',
      parameters: [
        { name: 'question', description: 'The question you want to ask the knowledge base', type: 'string', required: true },
      ],
      createdAt: '2024-11-03T10:00:00Z',
    },
    {
      id: 'CMD-SYS-004',
      name: 'mark_as_solve',
      description: 'Mark a forum thread as solved. Analyzes the conversation and SAVES it as a RAG entry to the knowledge base. Updates dashboard status. Requires Admin role.',
      parameters: [],
      createdAt: '2024-11-03T10:05:00Z',
    },
    {
      id: 'CMD-SYS-005',
      name: 'set_forums_id',
      description: 'Set the support forum channel ID that the bot monitors for new posts. Saves to bot_settings.json file. Requires Admin role.',
      parameters: [
        { name: 'channel_id', description: 'The Discord channel ID (right-click channel → Copy ID)', type: 'string', required: true },
      ],
      createdAt: '2024-11-03T11:00:00Z',
    },
    {
      id: 'CMD-SYS-006',
      name: 'set_satisfaction_delay',
      description: 'Set the delay (in seconds) before bot analyzes user satisfaction. Default: 15s. Range: 5-300s. Requires Admin role.',
      parameters: [
        { name: 'seconds', description: 'Delay in seconds (5-300)', type: 'number', required: true },
      ],
      createdAt: '2024-11-03T11:05:00Z',
    },
    {
      id: 'CMD-SYS-007',
      name: 'set_temperature',
      description: 'Set AI response temperature (0.0-2.0). Lower = consistent, Higher = creative. Default: 1.0. Requires Admin role.',
      parameters: [
        { name: 'temperature', description: 'Temperature value (0.0-2.0)', type: 'number', required: true },
      ],
      createdAt: '2024-11-03T11:10:00Z',
    },
    {
      id: 'CMD-SYS-008',
      name: 'set_max_tokens',
      description: 'Set maximum tokens for AI responses (100-8192). Controls response length. Default: 2048. Requires Admin role.',
      parameters: [
        { name: 'max_tokens', description: 'Max tokens (100-8192)', type: 'number', required: true },
      ],
      createdAt: '2024-11-03T11:15:00Z',
    },
    {
      id: 'CMD-SYS-009',
      name: 'status',
      description: 'Check bot status including loaded data, AI settings, active timers, and configuration. Requires Admin role.',
      parameters: [],
      createdAt: '2024-11-03T11:20:00Z',
    },
    {
      id: 'CMD-SYS-010',
      name: 'check_rag_entries',
      description: 'List all loaded RAG knowledge base entries with titles and keywords. Useful for debugging. Requires Admin role.',
      parameters: [],
      createdAt: '2024-11-03T11:25:00Z',
    },
    {
      id: 'CMD-SYS-011',
      name: 'check_auto_entries',
      description: 'List all loaded auto-responses with triggers and previews. Useful for debugging. Requires Admin role.',
      parameters: [],
      createdAt: '2024-11-03T11:30:00Z',
    },
];

const initialBotSettings: BotSettings = {
    systemPrompt: `You are the official support bot for Revolution Macro - a professional automation application designed for game macroing and task automation.

KEY FEATURES OF REVOLUTION MACRO:
- Automated gathering and resource collection
- Smart pathing and navigation systems
- Task scheduling and prioritization
- Auto-deposit and inventory management
- License key activation and management
- Custom script support and configuration
- Anti-AFK and safety features
- Multi-instance support

COMMON ISSUES USERS FACE:
- Character resetting during tasks (usually auto-deposit conflicts)
- Initialization errors (corrupt config files)
- License activation limits (HWID management)
- Antivirus false positives (requires exceptions)
- Pathing stuck/navigation issues (navmesh recalculation needed)
- Settings not saving (file permissions)
- Game window detection (must use windowed mode)

YOUR ROLE:
1. Provide clear, step-by-step solutions
2. Use the knowledge base context when available
3. Be friendly but professional
4. If uncertain, acknowledge it honestly
5. Encourage users to ask follow-up questions
6. Never make up features that don't exist

RESPONSE GUIDELINES:
- Keep answers concise (2-4 paragraphs max)
- Use numbered steps for troubleshooting
- Reference specific settings/tabs when relevant
- Acknowledge if the question is complex and may need human support
- Always be encouraging and supportive`,
    updatedAt: new Date().toISOString(),
};

export const useMockData = () => {
    // Start with empty arrays - API will populate, prevents flashing
    const [forumPosts, setForumPosts] = useState<ForumPost[]>([]);
    const [ragEntries, setRagEntries] = useState<RagEntry[]>([]);
    const [autoResponses, setAutoResponses] = useState<AutoResponse[]>([]);
    // Initialize with default commands immediately so they show up
    const [slashCommands, setSlashCommands] = useState<SlashCommand[]>(initialSlashCommands);
    const [botSettings, setBotSettings] = useState<BotSettings>(initialBotSettings);
    
    // Track if we've loaded from API to prevent sync during initial load
    const [isLoading, setIsLoading] = useState(true);

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
                    // Always use API data (even if empty) - this is the source of truth
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
                    // Load slash commands - always use latest from initial if we have more defined
                    if (data.slashCommands && Array.isArray(data.slashCommands) && data.slashCommands.length >= initialSlashCommands.length) {
                        setSlashCommands(data.slashCommands);
                        console.log(`✓ Loaded ${data.slashCommands.length} slash commands from API`);
                    } else {
                        // Use initial commands if API has fewer (means we added new commands)
                        setSlashCommands(initialSlashCommands);
                        console.log(`✓ Using updated slash commands (${initialSlashCommands.length} commands) - API has ${data.slashCommands?.length || 0}, will sync latest`);
                        // Force sync the new commands to API immediately
                        try {
                            await dataService.saveData(data.ragEntries || [], data.autoResponses || [], initialSlashCommands, data.botSettings || initialBotSettings);
                            console.log(`✓ Synced ${initialSlashCommands.length} slash commands to API`);
                        } catch (err) {
                            console.error('Failed to sync new slash commands:', err);
                        }
                    }
                    // Load bot settings
                    if (data.botSettings && typeof data.botSettings === 'object') {
                        setBotSettings(data.botSettings);
                        console.log(`✓ Loaded bot settings from API`);
                    } else {
                        console.log(`✓ Using default bot settings - will sync to API`);
                    }
                    hasLoaded = true;
                    setIsLoading(false); // Mark as loaded, now allow sync
                }
            } catch (error) {
                console.error('Failed to load data from API, using local defaults:', error);
                // Only use defaults if API fails - this is fallback behavior
                if (isMounted) {
                    setRagEntries(initialRagEntries);
                    setAutoResponses(initialAutoResponses);
                    setSlashCommands(initialSlashCommands);
                    setBotSettings(initialBotSettings);
                }
                hasLoaded = true;
                setIsLoading(false);
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

    // Sync data to API whenever RAG entries, auto-responses, slash commands, or bot settings change (with debounce)
    // IMPORTANT: Only sync after initial load is complete to prevent overwriting API data
    useEffect(() => {
        // Don't sync if we're still loading initial data from API
        if (isLoading) {
            return;
        }
        
        // Debounce to prevent excessive API calls
        const timeoutId = setTimeout(() => {
            const syncData = async () => {
                try {
                    console.log(`💾 Syncing to API: ${ragEntries.length} RAG entries, ${autoResponses.length} auto-responses, ${slashCommands.length} slash commands, bot settings`);
                    await dataService.saveData(ragEntries, autoResponses, slashCommands, botSettings);
                    console.log(`✓ Successfully synced to API`);
                } catch (error) {
                    console.error('Failed to sync data to API:', error);
                }
            };
            syncData();
        }, 1000); // 1 second debounce
        
        return () => clearTimeout(timeoutId);
    }, [ragEntries, autoResponses, slashCommands, botSettings, isLoading]);

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

    return { forumPosts, setForumPosts, ragEntries, setRagEntries, autoResponses, setAutoResponses, slashCommands, setSlashCommands, botSettings, setBotSettings };
};