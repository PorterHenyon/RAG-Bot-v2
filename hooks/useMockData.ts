import { useState, useEffect, useRef } from 'react';
import { ForumPost, RagEntry, PostStatus, AutoResponse, Message, SlashCommand, BotSettings, PendingRagEntry } from '../types';
import { dataService } from '../services/dataService';

// RAG entries initial data - Updated from export on 2025-11-28
const initialRagEntries: RagEntry[] = [
    {
        id: 'RAG-1764252942822',
        title: 'Resolving Display/Rendering Issues by Changing Font',
        content: "When encountering visual anomalies, display glitches, text corruption, or general rendering problems within an application or operating system, the root cause can sometimes be related to the currently active font. The provided solution indicates that changing the font to an alternative one successfully resolved the problem. This suggests that the previously used font might have been corrupted, incompatible, or caused rendering conflicts with the system or application.\n\n**Solution:**\nTo address such issues, users should navigate to the display settings of the operating system or the specific application where font choices are managed. Select a different, known-good font from the available options. Applying this change may alleviate the display or rendering problem.",
        keywords: ['font', 'display issue', 'rendering problem', 'text corruption', 'UI glitch', 'visual anomaly', 'troubleshooting', 'change font', 'font settings', 'font compatibility', 'display settings', 'fix'],
        createdAt: '2025-11-27T14:15:42.822Z',
        createdBy: 'Auto-generated',
    },
    {
        id: 'RAG-1764252896212',
        title: 'Fix for Macro Reset After Pine Tree Honey Collection',
        content: "If your automation macro resets after gathering honey at the Pine Tree and fails to reach your hive, often stopping near the mushroom field, this issue is typically caused by low-tier gear. To resolve this problem, you need to acquire and equip the Mountain Top Glider. This specific item provides the necessary travel speed or capacity for your macro to successfully complete its route from the Pine Tree field back to your hive without interruption.",
        keywords: ['Macro reset', 'Pine Tree', 'Glider', 'Mountain Top Glider', 'Low tier gear', 'Hive', 'Mushroom field', 'Automation', 'Honey collection', 'Travel path', 'Macro stuck'],
        createdAt: '2025-11-27T14:14:56.212Z',
        createdBy: 'Auto-generated',
    },
    {
        id: 'RAG-1764252884996',
        title: 'Fix for Flickering Screen Caused by Rendering Mode',
        content: "If you are experiencing a flickering screen, the issue is likely caused by an incorrect rendering mode setting. Follow these steps to resolve it:\n\n**Step-by-step fix:**\n1.  Download and install 'voidstrap'.\n2.  Open your 'fastflag settings'.\n3.  Navigate to the 'rendering and graphics' section.\n4.  Set the 'rendering mode' to 'automatic' or 'Direct3D 11'.",
        keywords: ['flickering screen', 'rendering mode', 'voidstrap', 'fastflag settings', 'Direct3D 11', 'graphics', 'display issue', 'automatic rendering'],
        createdAt: '2025-11-27T14:14:44.996Z',
        createdBy: 'Auto-generated',
    },
    {
        id: 'RAG-1763513969604',
        title: 'Enable Manual Control for Planter Schedule Sections',
        content: "If you are unable to delete or add sections to your planter schedule, it is likely because the system is currently operating in an 'automatic' or 'enabled' mode. To gain manual control and allow for modifications (adding or deleting sections), you need to disable the 'automatic' setting. Locate the option that controls this automatic functionality and turn it off. This action should switch the system to a 'manual' mode, enabling you to manage your planter schedule sections as needed.",
        keywords: ['planter', 'schedule', 'delete section', 'add section', 'automatic', 'manual control', 'disable automatic', 'planter management'],
        createdAt: '2025-11-19T00:59:29.604Z',
        createdBy: 'Auto-generated',
    },
    {
        id: 'RAG-1763513721274',
        title: 'Resolving Macro Issues in Fullscreen Games: Set Display Scaling to 100%',
        content: "Users may encounter errors or unexpected behavior when starting the macro in fullscreen games. This problem often occurs when Windows display scaling is set to a value other than 100%. To fix this:\n\n1.  **Open Display Settings:** Right-click on your desktop and select 'Display settings'.\n2.  **Adjust Scaling:** Under the 'Scale & layout' section, find the dropdown menu labeled 'Change the size of text, apps, and other items'.\n3.  **Set to 100%:** Change this value to '100% (Recommended)'.\n4.  **Restart Applications:** After applying the change, it is recommended to restart any running games and your macro software to ensure the new scaling setting is fully active.\n\nSetting display scaling to 100% helps applications, especially games, render and interact with input devices at their native resolution without interference from Windows scaling, which can cause issues with macro recognition or execution.\n**And make sure Roblox isn't in fullscreen mode**",
        keywords: ['full', 'fullscreen', 'display', '100%', 'scaling', 'input', 'scaling', 'resolution'],
        createdAt: '2025-11-19T00:55:21.274Z',
        createdBy: 'Auto-generated',
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
      createdAt: '2025-01-15T10:00:00Z',
    },
    {
      id: 'CMD-SYS-002',
      name: 'stop',
      description: 'Stops the bot process gracefully. Requires Admin role.',
      parameters: [],
      createdAt: '2025-01-15T10:05:00Z',
    },
    {
      id: 'CMD-SYS-003',
      name: 'ask',
      description: 'Ask the bot a question using the RAG knowledge base. Staff can use this to quickly find answers. Requires Admin role.',
      parameters: [
        { name: 'question', description: 'The question you want to ask the knowledge base', type: 'string', required: true },
      ],
      createdAt: '2025-01-20T10:00:00Z',
    },
    {
      id: 'CMD-SYS-004',
      name: 'mark_as_solved_with_review',
      description: 'Mark a forum thread as solved. Analyzes the conversation and SAVES it as a RAG entry to the knowledge base. Updates dashboard status. Requires Admin role.',
      parameters: [],
      createdAt: '2025-01-20T10:05:00Z',
    },
    {
      id: 'CMD-SYS-004B',
      name: 'mark_as_solved',
      description: 'Mark thread as solved and lock it WITHOUT creating a RAG entry. Just closes the thread. Requires Admin role.',
      parameters: [],
      createdAt: '2025-01-20T10:06:00Z',
    },
    {
      id: 'CMD-SYS-005',
      name: 'set_forums_id',
      description: 'Set the support forum channel ID that the bot monitors for new posts. Saves to bot_settings.json file. Requires Admin role.',
      parameters: [
        { name: 'channel_id', description: 'The Discord channel ID (right-click channel → Copy ID)', type: 'string', required: true },
      ],
      createdAt: '2025-01-22T11:00:00Z',
    },
    {
      id: 'CMD-SYS-005B',
      name: 'set_ignore_post_id',
      description: 'Add a post ID to the ignore list (e.g., rules post). Bot will not respond to ignored posts. Requires Admin role.',
      parameters: [
        { name: 'post_id', description: 'The post/thread ID to ignore (right-click thread → Copy ID)', type: 'string', required: true },
      ],
      createdAt: '2025-01-22T11:01:00Z',
    },
    {
      id: 'CMD-SYS-005C',
      name: 'set_unsolved_tag_id',
      description: 'Set the Discord tag ID for "Unsolved" posts. New posts will auto-tag as unsolved. Requires Admin role.',
      parameters: [
        { name: 'tag_id', description: 'The Discord tag ID (right-click tag → Copy ID)', type: 'string', required: true },
      ],
      createdAt: '2025-01-22T11:02:00Z',
    },
    {
      id: 'CMD-SYS-005D',
      name: 'set_resolved_tag_id',
      description: 'Set the Discord tag ID for "Resolved" posts. Solved posts will auto-tag as resolved. Requires Admin role.',
      parameters: [
        { name: 'tag_id', description: 'The Discord tag ID (right-click tag → Copy ID)', type: 'string', required: true },
      ],
      createdAt: '2025-01-22T11:03:00Z',
    },
    {
      id: 'CMD-SYS-006',
      name: 'set_satisfaction_delay',
      description: 'Set the delay (in seconds) before bot analyzes user satisfaction. Default: 15s. Range: 5-300s. Requires Admin role.',
      parameters: [
        { name: 'seconds', description: 'Delay in seconds (5-300)', type: 'number', required: true },
      ],
      createdAt: '2025-01-25T11:05:00Z',
    },
    {
      id: 'CMD-SYS-007',
      name: 'set_temperature',
      description: 'Set AI response temperature (0.0-2.0). Lower = consistent, Higher = creative. Default: 1.0. Requires Admin role.',
      parameters: [
        { name: 'temperature', description: 'Temperature value (0.0-2.0)', type: 'number', required: true },
      ],
      createdAt: '2025-01-28T11:10:00Z',
    },
    {
      id: 'CMD-SYS-008',
      name: 'set_max_tokens',
      description: 'Set maximum tokens for AI responses (100-8192). Controls response length. Default: 2048. Requires Admin role.',
      parameters: [
        { name: 'max_tokens', description: 'Max tokens (100-8192)', type: 'number', required: true },
      ],
      createdAt: '2025-01-28T11:15:00Z',
    },
    {
      id: 'CMD-SYS-009',
      name: 'status',
      description: 'Check bot status including loaded data, AI settings, active timers, and configuration. Requires Admin role.',
      parameters: [],
      createdAt: '2025-02-01T11:20:00Z',
    },
    {
      id: 'CMD-SYS-010',
      name: 'check_rag_entries',
      description: 'List all loaded RAG knowledge base entries with titles and keywords. Useful for debugging. Requires Admin role.',
      parameters: [],
      createdAt: '2025-02-01T11:25:00Z',
    },
    {
      id: 'CMD-SYS-011',
      name: 'check_auto_entries',
      description: 'List all loaded auto-responses with triggers and previews. Useful for debugging. Requires Admin role.',
      parameters: [],
      createdAt: '2025-02-02T11:30:00Z',
    },
    {
      id: 'CMD-SYS-012',
      name: 'api_info',
      description: 'View sensitive API configuration including URLs and system prompt details. PRIVATE - only you can see. Requires Admin role.',
      parameters: [],
      createdAt: '2025-02-02T11:35:00Z',
    },
    {
      id: 'CMD-SYS-013',
      name: 'set_post_inactivity_time',
      description: 'Set the hours before old unsolved posts are escalated to High Priority. Default: 12 hours. Range: 1-168 hours (7 days). Requires Admin role.',
      parameters: [
        { name: 'hours', description: 'Hours of inactivity before escalation (1-168)', type: 'number', required: true },
      ],
      createdAt: '2025-02-03T11:40:00Z',
    },
    {
      id: 'CMD-SYS-014',
      name: 'set_solved_post_retention',
      description: 'Set the days to keep solved/closed posts before automatic deletion. Default: 30 days. Range: 1-365 days. Cleanup runs daily. Requires Admin role.',
      parameters: [
        { name: 'days', description: 'Days to retain solved posts (1-365)', type: 'number', required: true },
      ],
      createdAt: '2025-02-03T11:45:00Z',
    },
    {
      id: 'CMD-SYS-015',
      name: 'search',
      description: 'Search for solved support forum posts containing your search term. Useful for finding solutions to similar problems. Requires Staff role.',
      parameters: [
        { name: 'query', description: 'The search term to look for in solved forum posts', type: 'string', required: true },
      ],
      createdAt: '2025-12-04T10:00:00Z',
    },
    {
      id: 'CMD-SYS-016',
      name: 'translate',
      description: 'Translate a message with smart detection. Non-English→English, or specify target language. REQUIRES message ID (no history permission needed). Requires Staff role.',
      parameters: [
        { name: 'message_id', description: 'REQUIRED: ID of message to translate (right-click → Copy ID)', type: 'string', required: true },
        { name: 'target_language', description: 'Optional: Target language (e.g., Spanish, French). Auto-detects if empty.', type: 'string', required: false },
      ],
      createdAt: '2025-12-04T10:05:00Z',
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
    const [pendingRagEntries, setPendingRagEntries] = useState<PendingRagEntry[]>([]);
    
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
                            await dataService.saveData(data.ragEntries || [], data.autoResponses || [], initialSlashCommands, data.botSettings || initialBotSettings, data.pendingRagEntries || []);
                            console.log(`✓ Synced ${initialSlashCommands.length} slash commands to API`);
                        } catch (err) {
                            console.error('Failed to sync new slash commands:', err);
                        }
                    }
                    // Load bot settings
                    if (data.botSettings && typeof data.botSettings === 'object') {
                        setBotSettings(data.botSettings);
                        // Also save to localStorage as backup
                        try {
                            localStorage.setItem('rag_bot_settings', JSON.stringify(data.botSettings));
                        } catch (e) {
                            console.error('Failed to save settings to localStorage:', e);
                        }
                        console.log(`✓ Loaded bot settings from API`);
                    } else {
                        // Try to load from localStorage as fallback
                        try {
                            const stored = localStorage.getItem('rag_bot_settings');
                            if (stored) {
                                const parsed = JSON.parse(stored);
                                if (parsed.systemPrompt) {
                                    setBotSettings(parsed);
                                    console.log(`✓ Loaded bot settings from localStorage (API had none)`);
                                } else {
                                    console.log(`✓ Using default bot settings - will sync to API`);
                                }
                            } else {
                                console.log(`✓ Using default bot settings - will sync to API`);
                            }
                        } catch (e) {
                            console.log(`✓ Using default bot settings - will sync to API`);
                        }
                    }
                    // Load pending RAG entries - with detailed logging
                    console.log('🔍 API Response Keys:', Object.keys(data));
                    console.log('🔍 Checking for pending RAG entries...', data.pendingRagEntries);
                    if (data.pendingRagEntries && Array.isArray(data.pendingRagEntries)) {
                        setPendingRagEntries(data.pendingRagEntries);
                        console.log(`✅ SET pending RAG entries in state: ${data.pendingRagEntries.length} entries`);
                        if (data.pendingRagEntries.length > 0) {
                            console.log(`📋 Pending entries details:`, JSON.stringify(data.pendingRagEntries, null, 2));
                        } else {
                            console.log(`ℹ API has pendingRagEntries array but it's empty []`);
                        }
                    } else {
                        console.error('❌ pendingRagEntries missing or not an array in API response!');
                        console.error('   Received:', typeof data.pendingRagEntries, data.pendingRagEntries);
                        setPendingRagEntries([]);
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
                    setPendingRagEntries([]);
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
        // Refresh forum posts every 30 seconds (reduced from 5s to save bandwidth)
        // Only poll when tab is visible to save resources
        const interval = setInterval(() => {
            if (isMounted && !document.hidden) {
                loadForumPosts();
            }
        }, 30000); // 30 seconds instead of 5
        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    // Sync data to API whenever RAG entries, auto-responses, slash commands, or bot settings change (with debounce)
    // IMPORTANT: Only sync after initial load is complete to prevent overwriting API data
    // Use refs to track previous values and only sync when data actually changes
    const prevDataRef = useRef<{rag: number, auto: number, commands: number, pending: number, settings: string, ragHash?: string, autoHash?: string} | null>(null);
    
    useEffect(() => {
        // Don't sync if we're still loading initial data from API
        if (isLoading) {
            return;
        }
        
        // Check if data actually changed by comparing counts AND content hashes
        const currentData = {
            rag: ragEntries.length,
            auto: autoResponses.length,
            commands: slashCommands.length,
            pending: pendingRagEntries.length,
            settings: JSON.stringify(botSettings),
            ragHash: JSON.stringify(ragEntries.map(r => r.id + r.title + r.content)), // Hash content to detect edits
            autoHash: JSON.stringify(autoResponses.map(a => a.id + a.name + a.responseText)) // Hash content to detect edits
        };
        
        // Skip if data hasn't actually changed
        if (prevDataRef.current && 
            prevDataRef.current.rag === currentData.rag &&
            prevDataRef.current.auto === currentData.auto &&
            prevDataRef.current.commands === currentData.commands &&
            prevDataRef.current.pending === currentData.pending &&
            prevDataRef.current.settings === currentData.settings &&
            prevDataRef.current.ragHash === currentData.ragHash &&
            prevDataRef.current.autoHash === currentData.autoHash) {
            return; // No changes, skip sync
        }
        
        // Update ref for next comparison
        prevDataRef.current = currentData;
        
        // Debounce to prevent excessive API calls - increased to 5 seconds
        // Only sync when tab is visible to save bandwidth
        const timeoutId = setTimeout(() => {
            const syncData = async () => {
                // Skip sync if tab is hidden to save bandwidth
                if (document.hidden) {
                    console.log('⏸ Skipping sync - tab is hidden');
                    return;
                }
                
                try {
                    // Save bot settings to localStorage as backup
                    try {
                        localStorage.setItem('rag_bot_settings', JSON.stringify(botSettings));
                    } catch (e) {
                        console.error('Failed to save settings to localStorage:', e);
                    }
                    
                    console.log(`💾 Syncing to API: ${ragEntries.length} RAG entries, ${autoResponses.length} auto-responses, ${slashCommands.length} slash commands, ${pendingRagEntries.length} pending RAG, bot settings`);
                    await dataService.saveData(ragEntries, autoResponses, slashCommands, botSettings, pendingRagEntries);
                    console.log(`✓ Successfully synced to API`);
                } catch (error) {
                    console.error('Failed to sync data to API:', error);
                }
            };
            syncData();
        }, 5000); // 5 second debounce (increased from 1s to reduce API calls)
        
        return () => clearTimeout(timeoutId);
    }, [ragEntries, autoResponses, slashCommands, botSettings, pendingRagEntries, isLoading]);

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

    return { forumPosts, setForumPosts, ragEntries, setRagEntries, autoResponses, setAutoResponses, slashCommands, setSlashCommands, botSettings, setBotSettings, pendingRagEntries, setPendingRagEntries };
};