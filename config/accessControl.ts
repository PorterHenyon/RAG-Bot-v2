// Access Control Configuration
// This controls who can access the dashboard

// ============================================
// OPTION 1: Whitelist Specific User IDs
// ============================================
// Add Discord User IDs of people who should have access
// How to get User IDs:
// 1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
// 2. Right-click a username → Copy User ID

export const ALLOWED_USER_IDS: string[] = [
    // Discord user IDs with dashboard access:
    '614865086804394012',  // Added user
];

// ============================================
// OPTION 2: Check Discord Server Membership
// ============================================
// Your Discord server ID (where your bot is)
// How to get Server ID:
// 1. Enable Developer Mode in Discord
// 2. Right-click your server icon → Copy Server ID

export const DISCORD_SERVER_ID = 'your_server_id_here';  // You'll need to provide this

// Note: Role checking requires a backend implementation
// For now, this is just client-side (can be bypassed)
// See HOW_TO_RESTRICT_ACCESS.md for backend implementation

// Set to true to require users to be members of your Discord server
export const REQUIRE_SERVER_MEMBERSHIP = true;

// ============================================
// OPTION 3: Role-Based Access (Backend Required)
// ============================================
// Role IDs that should have admin access
// Note: This requires backend implementation to work securely

export const ALLOWED_ROLE_IDS: string[] = [
    '1422106035337826315',  // Staff role
    '1405246916760961125',  // Additional authorized role
];

// Role names (for reference only, backend should check by ID)
export const ALLOWED_ROLE_NAMES = [
    'Admin',
    'Moderator',
    'Staff',
];

// ============================================
// General Settings
// ============================================
export const ACCESS_CONTROL = {
    // Enable access control checks
    ENABLED: true,
    
    // If true, allows anyone when ALLOWED_USER_IDS is empty
    // Set to false for production!
    ALLOW_ALL_IF_EMPTY: true,
    
    // Error messages
    MESSAGES: {
        ACCESS_DENIED: 'Access Denied: You do not have permission to access this dashboard.',
        NOT_IN_SERVER: 'You must be a member of our Discord server to access this dashboard.',
        INSUFFICIENT_ROLE: 'You do not have the required role to access this dashboard.',
        CONTACT_ADMIN: 'Please contact a server administrator for access.',
    },
};

// ============================================
// Helper Functions
// ============================================

export function isUserAllowed(userId: string): boolean {
    // If access control is disabled, allow everyone
    if (!ACCESS_CONTROL.ENABLED) {
        return true;
    }
    
    // If no user IDs specified and ALLOW_ALL_IF_EMPTY is true, allow everyone
    if (ALLOWED_USER_IDS.length === 0 && ACCESS_CONTROL.ALLOW_ALL_IF_EMPTY) {
        return true;
    }
    
    // Check if user ID is in allowed list
    return ALLOWED_USER_IDS.includes(userId);
}

export function getAccessDeniedMessage(): string {
    return `${ACCESS_CONTROL.MESSAGES.ACCESS_DENIED}\n\n${ACCESS_CONTROL.MESSAGES.CONTACT_ADMIN}`;
}

