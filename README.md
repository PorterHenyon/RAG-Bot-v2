# Discord RAG Bot with Dashboard

A Discord bot with a web dashboard for managing RAG (Retrieval-Augmented Generation) entries and auto-responses. The dashboard syncs with the bot in real-time, allowing you to continuously improve the bot's knowledge base.

## Features

- 🤖 **Discord Bot**: Automatically responds to forum posts using RAG and AI
- 📊 **Web Dashboard**: Manage RAG entries and auto-responses through a beautiful UI
- 🔄 **Real-time Sync**: Dashboard changes automatically sync to the bot
- 🎯 **Smart Matching**: Keyword-based matching with relevance scoring
- 🧠 **AI-Powered**: Uses Google Gemini AI for intelligent responses

## Architecture

- **Frontend**: React + TypeScript + Vite (deployed on Vercel)
- **Backend API**: Vercel Serverless Functions
- **Discord Bot**: Python with discord.py
- **AI**: Google Gemini API

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd RAG-Bot-v2
npm install
pip install -r requirements.txt
```

### 2. Environment Variables

#### For the Dashboard (Vercel):

Create a `.env` file or set in Vercel dashboard:
```env
VITE_API_URL=https://your-app.vercel.app/api
```

#### For the Bot:

Create a `.env` file in the root:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
SUPPORT_FORUM_CHANNEL_ID=your_channel_id
DATA_API_URL=https://your-app.vercel.app/api/data
```

### 3. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token
5. Enable these intents:
   - Message Content Intent
   - Server Members Intent
6. Invite bot to your server with appropriate permissions

### 4. Deploy Dashboard to Vercel

1. Push code to GitHub
2. Import project in Vercel
3. Set build command: `npm run build`
4. Set output directory: `dist`
5. Add environment variables in Vercel dashboard
6. Deploy!

### 5. Update Bot Configuration

After deploying to Vercel, update your bot's `.env` file:
```env
DATA_API_URL=https://your-actual-vercel-url.vercel.app/api/data
```

### 6. Run the Bot

```bash
python bot.py
```

The bot will:
- Fetch initial data from the dashboard API
- Sync data every 5 minutes automatically
- Respond to new forum posts in your configured channel

## Usage

### Dashboard

1. Access your dashboard at `https://your-app.vercel.app`
2. Navigate to "RAG Management"
3. Add/Edit/Delete RAG entries and auto-responses
4. Changes automatically sync to the bot within 5 minutes
5. Use `/reload` command in Discord to force immediate sync

### Bot Commands

- `/reload` - Manually reload data from dashboard (Admin only)
- `/stop` - Stop the bot gracefully (Admin only)

## File Structure

```
├── api/
│   └── data.ts              # Vercel API route for data sync
├── components/              # React components
├── services/
│   ├── dataService.ts       # API service for dashboard
│   └── geminiService.ts     # Gemini AI service
├── hooks/
│   └── useMockData.ts       # Data management hook
├── bot.py                   # Discord bot
├── requirements.txt         # Python dependencies
└── package.json             # Node dependencies
```

## How Syncing Works

1. **Dashboard → Bot**: 
   - Dashboard saves changes to Vercel API
   - Bot polls API every 5 minutes
   - Bot updates its internal database

2. **Bot → Dashboard**:
   - Bot uses current data for responses
   - Dashboard fetches data on load
   - Both stay in sync automatically

## Important Notes

⚠️ **Current Implementation**: The API uses in-memory storage, which resets on serverless function restarts. For production, you should:

- Use a database (Supabase, MongoDB Atlas, or Vercel Postgres)
- Implement proper authentication
- Add rate limiting
- Use environment variables for sensitive data

## Troubleshooting

### Bot not responding?
- Check bot is online in Discord
- Verify channel ID is correct
- Check bot has permissions in the channel

### Data not syncing?
- Verify `DATA_API_URL` in bot's `.env` matches your Vercel URL
- Check API is accessible: `curl https://your-app.vercel.app/api/data`
- Check bot logs for error messages

### Dashboard not loading?
- Verify build completed successfully
- Check Vercel deployment logs
- Ensure environment variables are set

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT
