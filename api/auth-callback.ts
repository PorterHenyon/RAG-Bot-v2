import type { VercelRequest, VercelResponse } from '@vercel/node';

const DISCORD_CLIENT_ID = process.env.VITE_DISCORD_CLIENT_ID;
const DISCORD_CLIENT_SECRET = process.env.DISCORD_CLIENT_SECRET;
const DISCORD_REDIRECT_URI = process.env.VITE_DISCORD_REDIRECT_URI;
const REQUIRED_ROLE_ID = '1422106035337826315'; // Staff role

export default async function handler(req: VercelRequest, res: VercelResponse) {
    const { code } = req.query;

    if (!code || typeof code !== 'string') {
        return res.status(400).json({ error: 'No authorization code provided' });
    }

    try {
        // Exchange code for access token
        const tokenResponse = await fetch('https://discord.com/api/oauth2/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                client_id: DISCORD_CLIENT_ID!,
                client_secret: DISCORD_CLIENT_SECRET!,
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: DISCORD_REDIRECT_URI!,
            }),
        });

        if (!tokenResponse.ok) {
            throw new Error('Failed to exchange code for token');
        }

        const tokens = await tokenResponse.json();

        // Get user info
        const userResponse = await fetch('https://discord.com/api/users/@me', {
            headers: {
                Authorization: `Bearer ${tokens.access_token}`,
            },
        });

        if (!userResponse.ok) {
            throw new Error('Failed to fetch user data');
        }

        const user = await userResponse.json();

        // Get user's guild member info (to check roles)
        const guildId = process.env.DISCORD_SERVER_ID;
        if (guildId) {
            const memberResponse = await fetch(
                `https://discord.com/api/users/@me/guilds/${guildId}/member`,
                {
                    headers: {
                        Authorization: `Bearer ${tokens.access_token}`,
                    },
                }
            );

            if (memberResponse.ok) {
                const member = await memberResponse.json();
                
                // Check if user has required role
                const hasRequiredRole = member.roles.includes(REQUIRED_ROLE_ID);
                
                if (!hasRequiredRole) {
                    return res.status(403).json({
                        error: 'Access denied',
                        message: 'You must have the Staff role to access this dashboard.',
                    });
                }
            } else {
                return res.status(403).json({
                    error: 'Not a server member',
                    message: 'You must be a member of the Discord server to access this dashboard.',
                });
            }
        }

        // Return user data if authorized
        return res.status(200).json({
            user: {
                id: user.id,
                username: user.username,
                discriminator: user.discriminator,
                avatar: user.avatar,
                email: user.email,
            },
        });

    } catch (error) {
        console.error('Auth callback error:', error);
        return res.status(500).json({ error: 'Authentication failed' });
    }
}

