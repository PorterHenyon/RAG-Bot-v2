// Vercel API route for managing RAG data
import type { VercelRequest, VercelResponse } from '@vercel/node';

interface RagEntry {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  createdAt: string;
  createdBy: string;
}

interface PendingRagEntry {
  id: string;
  title: string;
  content: string;
  keywords: string[];
  createdAt: string;
  source: string;
  threadId: string;
  conversationPreview: string;
}

interface AutoResponse {
  id: string;
  name: string;
  triggerKeywords: string[];
  responseText: string;
  createdAt: string;
}

interface CommandParameter {
  name: string;
  description: string;
  type: 'string' | 'number' | 'boolean' | 'user' | 'channel' | 'role';
  required: boolean;
}

interface SlashCommand {
  id: string;
  name: string;
  description: string;
  parameters: CommandParameter[];
  createdAt: string;
}

interface BotSettings {
  systemPrompt?: string;
  updatedAt?: string;
  support_forum_channel_id?: number | string;
  satisfaction_delay?: number;
  satisfaction_analysis_enabled?: boolean;
  ai_temperature?: number;
  ai_max_tokens?: number;
  ignored_post_ids?: string[];
  post_inactivity_hours?: number;
  high_priority_check_interval_hours?: number;
  solved_post_retention_days?: number;
  unsolved_tag_id?: number | string | null;
  resolved_tag_id?: number | string | null;
  auto_rag_enabled?: boolean;
  support_notification_channel_id?: number | string;
  support_role_id?: number | string | null;
  last_updated?: string;
  [key: string]: any;  // Allow any additional settings
}

interface DataStore {
  ragEntries: RagEntry[];
  autoResponses: AutoResponse[];
  slashCommands: SlashCommand[];
  botSettings: BotSettings;
  pendingRagEntries: PendingRagEntry[];
}

// Persistent storage using Vercel KV (Redis)
// Falls back to in-memory if KV not configured
let kvClient: any = null;
let inMemoryStore: DataStore = {
  ragEntries: [
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
    },
    {
      id: 'RAG-WEREWOLF-001',
      title: 'Werewolves Kill Bees - Bee Swarm Simulator Game Mechanic',
      content: "**CRITICAL: Werewolves KILL Bees in Bee Swarm Simulator**\n\nWerewolves are hostile mobs that spawn in fields and **actively attack and kill your bees**. This is a fundamental game mechanic - werewolves killing bees is NORMAL gameplay, not a bug.\n\n**What Happens:**\n- Werewolves spawn periodically in various fields\n- When a werewolf encounters your bees, it attacks and kills them\n- Your bee count decreases when bees are killed\n- This can interrupt macro automation, causing field changes or resets\n\n**Solutions:**\n1. Upgrade defense equipment (masks, guards, boots) to protect bees\n2. Configure macro to avoid fields where werewolves frequently spawn\n3. Monitor bee count - significant drops indicate werewolf attacks\n4. Ensure macro can defeat werewolves before they kill too many bees\n\n**Important:** Bee deaths from werewolves are expected game behavior. Upgrade equipment or adjust macro settings to handle werewolf encounters.",
      keywords: ['werewolf', 'werewolves', 'bees killed', 'bee death', 'macro interruption', 'hostile mob', 'BSS', 'equipment', 'defense'],
      createdAt: new Date().toISOString(),
      createdBy: 'Manual Entry',
    },
    {
      id: 'RAG-BSS-MECHANICS-001',
      title: 'Bee Swarm Simulator Core Game Mechanics',
      content: "**BEE SWARM SIMULATOR - ESSENTIAL MECHANICS:**\n\n**Core Gameplay:**\n- Collect pollen from fields using tools and bees\n- Convert pollen to honey at hive (primary currency)\n- Use honey to purchase upgrades, eggs, equipment\n- Expand hive by hatching eggs\n\n**Bees:**\n- Rarities: Common, Rare, Epic, Legendary, Mythic, Event\n- Each bee has unique abilities (pollen collection, combat, special effects)\n- Upgrade/transform bees using Royal Jelly\n\n**Fields:**\n- Multiple fields with different pollen types (Red, Blue, White, Colorless)\n- Fields: Sunflower, Dandelion, Clover, Spider, Strawberry, Bamboo, Pineapple Patch, Pine Tree Forest, Cactus, Rose, Mountain Top, Coconut, Pepper Patch, Stump Field, and more\n- Higher-level fields = more pollen but stronger mobs\n\n**Hostile Mobs:**\n- **Werewolves:** Spawn in fields, attack and KILL your bees (normal gameplay)\n- **Vicious Bees:** Periodic spawns that can kill bees if not defeated\n- **Field Mobs:** Ladybugs, Rhino Beetles, Mantises, Spiders guard fields\n- Mobs drop loot when defeated (often required for quests)\n- **Bee deaths from mobs/werewolves/vicious bees are NORMAL**\n\n**Planters:**\n- Blue Clay, Red Clay, Plastic, Cactus, Petal planters\n- Produce nectar over time (provides buffs)\n- Require placement, watering, harvesting (manual or macro)\n\n**Equipment:**\n- Masks: Increase pollen collection, provide abilities\n- Guards: Provide defense, reduce bee deaths\n- Boots: Increase movement speed, special abilities\n- Amulets: Stat boosts and special effects\n- Higher-tier equipment = better efficiency\n\n**Quests & NPCs:**\n- Black Bear: Main quest giver\n- Mother Bear: Quest rewards\n- Spirit Bear: Advanced quests with better rewards\n- Completing quests rewards honey, tickets, items, rare bees",
      keywords: ['BSS', 'bee swarm simulator', 'game mechanics', 'bees', 'fields', 'pollen', 'honey', 'planters', 'equipment', 'mobs', 'werewolves', 'vicious bee', 'quests', 'NPCs', 'bee death'],
      createdAt: new Date().toISOString(),
      createdBy: 'Research-Based Entry',
    },
    {
      id: 'RAG-REVOLUTION-MACRO-001',
      title: 'Revolution Macro Features and Troubleshooting',
      content: "**REVOLUTION MACRO - FEATURES & TROUBLESHOOTING:**\n\n**Core Features:**\n- AI-powered automation for Bee Swarm Simulator\n- Cross-platform: Windows 10/11 and newer macOS\n- Modern .NET 8.0/WPF interface\n- Discord integration for notifications\n\n**Key Features:**\n- **AI Gather:** Vision-based token detection and collection, adapts to field layouts\n- **Vic Hop:** Server-hopping to locate/defeat vicious bees, supports alt coordination\n- **Planter Studio:** Automated planter management (planting, watering, harvesting, rotation)\n- **RBC Gather:** Automated alt coordination during Robo-bear Challenge events\n- **AI Stinger Hop:** Server hopping with AI detection for optimal farming\n- **AI Pathfinding:** Optimized routes using shortcuts (portals, cannons)\n- **Standard Features:** Pattern gathering, auto-conversion, hive claiming, field navigation, quest automation, dispenser collection\n- **RDP Support:** Full Remote Desktop Protocol support for alt account automations\n\n**Common Issues & Solutions:**\n- **Macro Reset:** Low-tier gear issue - upgrade equipment (especially gliders for travel speed)\n- **Pathfinding Problems:** Check field navigation settings, may need navmesh recalculation\n- **Bee Death Interruptions:** Werewolves/mobs killing bees is normal - upgrade defense equipment or configure macro to handle mobs\n- **Display/Rendering Issues:** Set display scaling to 100%, ensure Roblox is in windowed mode (not fullscreen)\n- **Initialization Errors:** Usually corrupt config files - reset configuration or reinstall\n- **Settings Not Saving:** Check file permissions, ensure macro has write access\n- **Game Window Detection:** Must use windowed mode - fullscreen causes detection issues\n- **Auto-Deposit Conflicts:** Character resetting often caused by auto-deposit conflicts - adjust timing or disable temporarily\n\n**Best Practices:**\n- Keep macro updated\n- Configure settings to match equipment and goals\n- Monitor bee count and adjust if deaths are excessive\n- Use appropriate fields for your bee/equipment level\n- Test settings before long AFK sessions",
      keywords: ['revolution macro', 'AI gather', 'vic hop', 'planter studio', 'RBC gather', 'AI pathfinding', 'troubleshooting', 'macro reset', 'bee death', 'display scaling', 'initialization error', 'auto-deposit', 'RDP'],
      createdAt: new Date().toISOString(),
      createdBy: 'Research-Based Entry',
    },
  ],
  autoResponses: [
    {
      id: 'AR-001',
      name: 'Password Reset',
      triggerKeywords: ['password', 'reset', 'forgot', 'lost account'],
      responseText: 'You can reset your password by visiting this link: [https://revolutionmacro.com/password-reset](https://revolutionmacro.com/password-reset).',
      createdAt: new Date().toISOString(),
    },
  ],
  slashCommands: [
    {
      id: 'CMD-SYS-001',
      name: 'reload',
      description: 'Reloads the bot\'s RAG database and auto-responses from the dashboard. Requires Admin role.',
      parameters: [],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-002',
      name: 'stop',
      description: 'Stops the bot process gracefully. Requires Admin role.',
      parameters: [],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-003',
      name: 'ask',
      description: 'Ask the bot a question using the RAG knowledge base. Staff can use this to quickly find answers. Requires Admin role.',
      parameters: [
        { name: 'question', description: 'The question you want to ask the knowledge base', type: 'string', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-004',
      name: 'mark_as_solved_with_review',
      description: 'Mark a forum thread as solved. Analyzes the conversation and SAVES it as a RAG entry to the knowledge base. Updates dashboard status. Requires Admin role.',
      parameters: [],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-004B',
      name: 'mark_as_solved',
      description: 'Mark thread as solved and lock it WITHOUT creating a RAG entry. Just closes the thread. Requires Admin role.',
      parameters: [],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-005',
      name: 'set_forums_id',
      description: 'Set the support forum channel ID that the bot monitors for new posts. Saves to bot_settings.json file. Requires Admin role.',
      parameters: [
        { name: 'channel_id', description: 'The Discord channel ID (right-click channel → Copy ID)', type: 'string', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-005B',
      name: 'set_ignore_post_id',
      description: 'Add a post ID to the ignore list (e.g., rules post). Bot will not respond to ignored posts. Requires Admin role.',
      parameters: [
        { name: 'post_id', description: 'The post/thread ID to ignore (right-click thread → Copy ID)', type: 'string', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-006',
      name: 'set_satisfaction_delay',
      description: 'Set the delay (in seconds) before bot analyzes user satisfaction. Default: 15s. Range: 5-300s. Requires Admin role.',
      parameters: [
        { name: 'seconds', description: 'Delay in seconds (5-300)', type: 'number', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-007',
      name: 'set_temperature',
      description: 'Set AI response temperature (0.0-2.0). Lower = consistent, Higher = creative. Default: 1.0. Requires Admin role.',
      parameters: [
        { name: 'temperature', description: 'Temperature value (0.0-2.0)', type: 'number', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-008',
      name: 'set_max_tokens',
      description: 'Set maximum tokens for AI responses (100-8192). Controls response length. Default: 2048. Requires Admin role.',
      parameters: [
        { name: 'max_tokens', description: 'Max tokens (100-8192)', type: 'number', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-009',
      name: 'status',
      description: 'Check bot status including loaded data, AI settings, active timers, and configuration. Requires Admin role.',
      parameters: [],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-010',
      name: 'check_rag_entries',
      description: 'List all loaded RAG knowledge base entries with titles and keywords. Useful for debugging. Requires Admin role.',
      parameters: [],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-011',
      name: 'check_auto_entries',
      description: 'List all loaded auto-responses with triggers and previews. Useful for debugging. Requires Admin role.',
      parameters: [],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-012',
      name: 'set_post_inactivity_time',
      description: 'Set the hours before old unsolved posts are escalated to High Priority. Default: 12 hours. Range: 1-168 hours (7 days). Requires Admin role.',
      parameters: [
        { name: 'hours', description: 'Hours of inactivity before escalation (1-168)', type: 'number', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-013',
      name: 'set_solved_post_retention',
      description: 'Set the days to keep solved/closed posts before automatic deletion. Default: 30 days. Range: 1-365 days. Cleanup runs daily. Requires Admin role.',
      parameters: [
        { name: 'days', description: 'Days to retain solved posts (1-365)', type: 'number', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
    {
      id: 'CMD-SYS-015',
      name: 'search',
      description: 'Search for solved support forum posts containing your search term. Useful for finding solutions to similar problems. Requires Staff role.',
      parameters: [
        { name: 'query', description: 'The search term to look for in solved forum posts', type: 'string', required: true },
      ],
      createdAt: new Date().toISOString(),
    },
  ],
  pendingRagEntries: [],
  botSettings: {
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
  },
};

// Initialize KV/Redis client if available (lazy import)
async function initKV() {
  if (kvClient) return; // Already initialized
  
  // Try Vercel KV first (REST API)
  if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
    try {
      const kvModule = await import('@vercel/kv');
      kvClient = kvModule.kv;
      console.log('✓ Using Vercel KV for persistent storage');
      return;
    } catch (e) {
      console.log('⚠ Vercel KV not available, trying direct Redis connection...');
    }
  }
  
  // Try direct Redis connection (Redis Cloud, etc.)
  // Check both REDIS_URL and STORAGE_URL (Vercel custom prefix)
  const redisUrl = process.env.REDIS_URL || process.env.STORAGE_URL;
  if (redisUrl) {
    try {
      const Redis = (await import('ioredis')).default;
      kvClient = new Redis(redisUrl);
      console.log('✓ Using direct Redis connection for persistent storage');
      
      // Test connection
      await kvClient.ping();
      return;
    } catch (e) {
      console.log('⚠ Redis connection failed:', e);
      kvClient = null;
    }
  }
  
  if (!kvClient) {
    console.log('⚠ No persistent storage configured, using in-memory storage (data won\'t persist)');
  }
}

// Helper functions to get/set data
// Leaderboard is now handled in the POST handler directly

async function getDataStore(): Promise<DataStore> {
  await initKV();
  if (kvClient) {
    try {
      // Check if using Vercel KV (has .get method) or direct Redis (has .get method)
      let ragEntries: any;
      let autoResponses: any;
      let slashCommands: any;
      let botSettings: any;
      let pendingRagEntries: any;
      
      if (typeof kvClient.get === 'function') {
        // Direct Redis (ioredis)
        ragEntries = await kvClient.get('rag_entries');
        autoResponses = await kvClient.get('auto_responses');
        slashCommands = await kvClient.get('slash_commands');
        botSettings = await kvClient.get('bot_settings');
        pendingRagEntries = await kvClient.get('pending_rag_entries');
        console.log('🔍 Raw pendingRagEntries from Redis:', pendingRagEntries);
        
        // Parse JSON if stored as strings
        if (typeof ragEntries === 'string') {
          try {
            ragEntries = JSON.parse(ragEntries);
          } catch (e) {
            console.error('Error parsing rag_entries JSON:', e);
            ragEntries = null;
          }
        }
        if (typeof autoResponses === 'string') {
          try {
            autoResponses = JSON.parse(autoResponses);
            console.log(`✓ Parsed auto_responses from JSON string: ${Array.isArray(autoResponses) ? autoResponses.length : 'not array'} entries`);
          } catch (e) {
            console.error('❌ Error parsing auto_responses JSON:', e);
            console.error(`   Raw value: ${autoResponses.substring(0, 200)}...`);
            autoResponses = null;
          }
        } else if (autoResponses === null || autoResponses === undefined) {
          console.log(`⚠ auto_responses is null/undefined in Redis`);
        } else {
          console.log(`✓ auto_responses from Redis: ${Array.isArray(autoResponses) ? autoResponses.length : typeof autoResponses} entries`);
        }
        
        if (typeof slashCommands === 'string') {
          try {
            slashCommands = JSON.parse(slashCommands);
          } catch (e) {
            console.error('Error parsing slash_commands JSON:', e);
            slashCommands = null;
          }
        }
        
        if (typeof botSettings === 'string') {
          try {
            botSettings = JSON.parse(botSettings);
          } catch (e) {
            console.error('Error parsing bot_settings JSON:', e);
            botSettings = null;
          }
        }
        
        if (typeof pendingRagEntries === 'string') {
          try {
            pendingRagEntries = JSON.parse(pendingRagEntries);
          } catch (e) {
            console.error('Error parsing pending_rag_entries JSON:', e);
            pendingRagEntries = null;
          }
        }
      } else {
        // Vercel KV (different API)
        ragEntries = await kvClient.get('rag_entries');
        autoResponses = await kvClient.get('auto_responses');
        slashCommands = await kvClient.get('slash_commands');
        botSettings = await kvClient.get('bot_settings');
        pendingRagEntries = await kvClient.get('pending_rag_entries');
        console.log('🔍 Raw pendingRagEntries from Vercel KV:', pendingRagEntries);
      }
      
      // Use stored data if available, otherwise fall back to in-memory
      // IMPORTANT: Only use fallback if we have NO persistent storage configured
      // If persistent storage exists but is empty, return empty arrays to avoid confusion
      const hasPersistentStorage = !!kvClient;
      
      let result: DataStore;
      
      if (hasPersistentStorage) {
        // We have persistent storage - use what's stored (even if empty)
        result = {
          ragEntries: (ragEntries && Array.isArray(ragEntries)) ? ragEntries : [],
          autoResponses: (autoResponses && Array.isArray(autoResponses)) ? autoResponses : [],
          slashCommands: (slashCommands && Array.isArray(slashCommands)) ? slashCommands : [],
          botSettings: (botSettings && typeof botSettings === 'object') ? botSettings : inMemoryStore.botSettings,
          pendingRagEntries: (pendingRagEntries && Array.isArray(pendingRagEntries)) ? pendingRagEntries : [],
        };
        
        console.log(`📊 Returning to frontend: ${result.ragEntries.length} RAG, ${result.autoResponses.length} auto, ${result.pendingRagEntries.length} pending`);
        if (result.pendingRagEntries.length > 0) {
          console.log('📋 Pending RAG entries being sent:', result.pendingRagEntries);
        }
        
        if (ragEntries && Array.isArray(ragEntries) && ragEntries.length > 0) {
          console.log(`✓ Loaded ${ragEntries.length} RAG entries from persistent storage`);
        } else {
          console.log(`⚠ No RAG entries found in persistent storage (database is empty)`);
        }
        
        if (autoResponses && Array.isArray(autoResponses) && autoResponses.length > 0) {
          console.log(`✓ Loaded ${autoResponses.length} auto-responses from persistent storage`);
        } else {
          console.log(`⚠ No auto-responses found in persistent storage (database is empty)`);
        }
      } else {
        // No persistent storage - use in-memory fallback
        result = {
          ragEntries: (ragEntries && Array.isArray(ragEntries) && ragEntries.length > 0) ? ragEntries : inMemoryStore.ragEntries,
          autoResponses: (autoResponses && Array.isArray(autoResponses) && autoResponses.length > 0) ? autoResponses : inMemoryStore.autoResponses,
          slashCommands: (slashCommands && Array.isArray(slashCommands) && slashCommands.length > 0) ? slashCommands : inMemoryStore.slashCommands,
          botSettings: (botSettings && typeof botSettings === 'object') ? botSettings : inMemoryStore.botSettings,
          pendingRagEntries: (pendingRagEntries && Array.isArray(pendingRagEntries) && pendingRagEntries.length > 0) ? pendingRagEntries : [],
        };
        
        console.log(`⚠ Using in-memory fallback data (persistent storage not configured)`);
        console.log(`   ⚠⚠⚠ WARNING: Data will be lost on redeploy! Configure Vercel KV or Redis.`);
      }
      
      return result;
    } catch (error) {
      console.error('Error reading from Redis/KV:', error);
      return inMemoryStore;
    }
  }
  console.log(`⚠ No persistent storage configured, using in-memory store (${inMemoryStore.ragEntries.length} RAG entries, ${inMemoryStore.autoResponses.length} auto-responses)`);
  return inMemoryStore;
}

async function saveDataStore(data: DataStore): Promise<void> {
  await initKV();
  if (kvClient) {
    try {
      // Check if using direct Redis (ioredis) or Vercel KV
      if (typeof kvClient.set === 'function') {
        // Direct Redis - store as JSON strings
        const ragJson = JSON.stringify(data.ragEntries);
        const autoJson = JSON.stringify(data.autoResponses);
        const commandsJson = JSON.stringify(data.slashCommands);
        const settingsJson = JSON.stringify(data.botSettings);
        const pendingJson = JSON.stringify(data.pendingRagEntries);
        console.log(`💾 Saving to Redis: rag_entries (${data.ragEntries.length}), auto_responses (${data.autoResponses.length}), slash_commands (${data.slashCommands.length}), pending_rag (${data.pendingRagEntries.length}), bot_settings`);
        await kvClient.set('rag_entries', ragJson);
        await kvClient.set('auto_responses', autoJson);
        await kvClient.set('slash_commands', commandsJson);
        await kvClient.set('bot_settings', settingsJson);
        await kvClient.set('pending_rag_entries', pendingJson);
        console.log(`✓ Saved all data including ${data.pendingRagEntries.length} pending RAG entries to Redis`);
        
        // Verify immediately after save
        const verifyRag = await kvClient.get('rag_entries');
        const verifyAuto = await kvClient.get('auto_responses');
        console.log(`🔍 Immediate verification: rag_entries exists: ${!!verifyRag}, auto_responses exists: ${!!verifyAuto}`);
        if (verifyAuto) {
          try {
            const parsed = JSON.parse(verifyAuto as string);
            console.log(`   ✓ auto_responses parsed: ${Array.isArray(parsed) ? parsed.length : 'not array'} entries`);
          } catch (e) {
            console.error(`   ❌ Failed to parse auto_responses: ${e}`);
          }
        }
      } else {
        // Vercel KV
        console.log(`💾 Saving to Vercel KV: all data including bot settings and pending RAG entries`);
        await kvClient.set('rag_entries', data.ragEntries);
        await kvClient.set('auto_responses', data.autoResponses);
        await kvClient.set('slash_commands', data.slashCommands);
        await kvClient.set('bot_settings', data.botSettings);
        await kvClient.set('pending_rag_entries', data.pendingRagEntries);
        console.log(`✓ Saved all data including ${data.pendingRagEntries.length} pending RAG entries to Vercel KV`);
      }
    } catch (error) {
      console.error('Error saving to Redis/KV:', error);
      throw error; // Re-throw so caller knows save failed
    }
  } else {
    inMemoryStore = data;
    console.log(`⚠ Saved to in-memory storage (will be lost on restart): ${data.ragEntries.length} RAG entries, ${data.autoResponses.length} auto-responses, ${data.slashCommands.length} slash commands, ${data.pendingRagEntries.length} pending RAG, bot settings`);
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method === 'GET') {
    // Return all data with caching to reduce bandwidth
    try {
      const data = await getDataStore();
      
      // Generate ETag from data hash for conditional requests
      const crypto = await import('crypto');
      const dataString = JSON.stringify(data);
      const etag = crypto.createHash('md5').update(dataString).digest('hex');
      
      // Check if client has cached version (conditional request)
      const clientEtag = req.headers['if-none-match'];
      if (clientEtag === etag) {
        // Data hasn't changed, return 304 Not Modified (saves bandwidth!)
        res.setHeader('ETag', etag);
        res.setHeader('Cache-Control', 'public, max-age=60, must-revalidate'); // Cache for 60 seconds
        return res.status(304).end();
      }
      
      // Log what we're returning for debugging
      console.log(`📤 GET /api/data returning: ${data.ragEntries.length} RAG entries, ${data.autoResponses.length} auto-responses, ${data.slashCommands.length} slash commands`);
      
      // Set caching headers
      res.setHeader('ETag', etag);
      res.setHeader('Cache-Control', 'public, max-age=60, must-revalidate'); // Cache for 60 seconds
      res.setHeader('Content-Type', 'application/json');
      
      return res.status(200).json(data);
    } catch (error) {
      console.error('Error fetching data:', error);
      // Only return inMemoryStore as last resort (when Redis fails)
      console.log(`⚠ Returning fallback in-memory data due to error`);
      return res.status(200).json(inMemoryStore);
    }
  }

  if (req.method === 'POST') {
    // Handle special actions like leaderboard updates
    if (req.body && typeof req.body === 'object' && 'action' in req.body) {
      const action = req.body.action;
      
      if (action === 'cleanup_pending_rag') {
        // Clear all pending RAG entries
        try {
          await initKV();
          if (!kvClient) {
            return res.status(400).json({ error: 'No persistent storage configured' });
          }
          
          const currentData = await getDataStore();
          currentData.pendingRagEntries = [];
          await saveDataStore(currentData);
          
          return res.status(200).json({
            success: true,
            message: 'Cleared all pending RAG entries'
          });
        } catch (error: any) {
          console.error('Error clearing pending RAG entries:', error);
          return res.status(500).json({ error: `Failed to clear pending RAG entries: ${error.message}` });
        }
      }

      if (action === 'update_leaderboard') {
        // Handle leaderboard update
        try {
          await initKV();
          const leaderboard = req.body.leaderboard;
          
          if (kvClient) {
            if (typeof kvClient.set === 'function') {
              // Direct Redis
              await kvClient.set('leaderboard', JSON.stringify(leaderboard));
            } else {
              // Vercel KV
              await kvClient.set('leaderboard', leaderboard);
            }
            console.log('✓ Leaderboard saved to persistent storage');
            return res.status(200).json({ success: true, message: 'Leaderboard updated' });
          } else {
            console.warn('⚠ No persistent storage for leaderboard');
            return res.status(200).json({ success: true, warning: 'No persistent storage configured' });
          }
        } catch (error) {
          console.error('Error saving leaderboard:', error);
          return res.status(500).json({ error: 'Failed to save leaderboard' });
        }
      }
    }
    
    // Update data
    try {
      await initKV(); // Ensure KV is initialized before saving
      
      const currentData = await getDataStore();
      const { ragEntries, autoResponses, slashCommands, botSettings, pendingRagEntries } = req.body as Partial<DataStore>;
      
      // Only update fields that are provided and valid
      const updatedData: DataStore = {
        ragEntries: (ragEntries && Array.isArray(ragEntries)) ? ragEntries : currentData.ragEntries,
        autoResponses: (autoResponses && Array.isArray(autoResponses)) ? autoResponses : currentData.autoResponses,
        slashCommands: (slashCommands && Array.isArray(slashCommands)) ? slashCommands : currentData.slashCommands,
        botSettings: (botSettings && typeof botSettings === 'object') ? botSettings : currentData.botSettings,
        pendingRagEntries: (pendingRagEntries && Array.isArray(pendingRagEntries)) ? pendingRagEntries : currentData.pendingRagEntries,
      };
      
      console.log(`📝 Saving data: ${updatedData.ragEntries.length} RAG entries, ${updatedData.autoResponses.length} auto-responses, ${updatedData.slashCommands.length} slash commands`);
      
      // Check if we have persistent storage before saving
      if (!kvClient) {
        console.error('❌ CRITICAL: No persistent storage configured! Data will be lost on redeploy.');
        console.error('   Please configure Vercel KV or Redis. See SETUP_VERCEL_KV.md for instructions.');
        // Still save to in-memory as fallback, but warn the user
        await saveDataStore(updatedData);
        return res.status(200).json({ 
          success: true, 
          data: updatedData,
          warning: 'No persistent storage configured. Data saved to memory only and will be lost on redeploy. Please configure Vercel KV or Redis.'
        });
      }
      
      console.log(`📝 Before save - RAG: ${updatedData.ragEntries.length}, Auto: ${updatedData.autoResponses.length}`);
      await saveDataStore(updatedData);
      
      // Verify the save by reading back (only if we have persistent storage)
      if (kvClient) {
        // Wait a brief moment to ensure Redis write is complete
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const verifyData = await getDataStore();
        console.log(`🔍 After save verification - RAG: ${verifyData.ragEntries.length}, Auto: ${verifyData.autoResponses.length}`);
        
        let verificationPassed = true;
        let errors: string[] = [];
        
        if (verifyData.ragEntries.length !== updatedData.ragEntries.length) {
          verificationPassed = false;
          errors.push(`RAG entries: expected ${updatedData.ragEntries.length}, got ${verifyData.ragEntries.length}`);
        }
        
        if (verifyData.autoResponses.length !== updatedData.autoResponses.length) {
          verificationPassed = false;
          errors.push(`Auto-responses: expected ${updatedData.autoResponses.length}, got ${verifyData.autoResponses.length}`);
          // Debug: Log what we actually got
          console.error(`❌ Auto-responses mismatch!`);
          console.error(`   Expected: ${updatedData.autoResponses.length} entries`);
          console.error(`   Got: ${verifyData.autoResponses.length} entries`);
          console.error(`   Expected IDs: ${updatedData.autoResponses.map(a => a.id).join(', ')}`);
          console.error(`   Got IDs: ${verifyData.autoResponses.map(a => a.id).join(', ')}`);
        }
        
        if (!verificationPassed) {
          console.error(`⚠ Data mismatch after save! ${errors.join(', ')}`);
          return res.status(500).json({ 
            error: 'Data verification failed after save',
            warning: `Data may not have persisted correctly: ${errors.join(', ')}`
          });
        } else {
          console.log(`✓ Data verified: ${verifyData.ragEntries.length} RAG entries and ${verifyData.autoResponses.length} auto-responses persisted successfully`);
        }
      }
      
      return res.status(200).json({ success: true, data: updatedData });
    } catch (error) {
      console.error('Error saving data:', error);
      return res.status(500).json({ error: `Failed to save data: ${error instanceof Error ? error.message : 'Unknown error'}` });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
