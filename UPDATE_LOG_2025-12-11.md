# Update Log - December 11, 2025

## 🐛 Bug Fixes
- **Fixed SolvedButton error** - Added missing `conversation` argument to all SolvedButton calls
- **Fixed reload command timeout** - Added immediate response and better error handling
- **Fixed bot blocking** - Made all sync operations non-blocking to prevent commands/forum posts from freezing

## 💰 Cost Optimizations
- **Added FORCE_KEYWORD_SEARCH option** - Completely disable embeddings to save Railway CPU (set `FORCE_KEYWORD_SEARCH=true`)
- **Query embedding cache** - Cache query embeddings to avoid re-encoding same queries (saves CPU)
- **Memory optimizations**:
  - Reduced query embedding cache: 100 → 50 entries
  - Reduced AI response cache: unlimited → 50 entries max
  - Truncate RAG content to 500 chars in memory (full content in Pinecone)
  - Thread images cleared after 2h (was 24h)
  - Cleanup runs every 3h (was 6h)
  - Auto-cleanup old leaderboard data

## 🌲 Pinecone Improvements
- **Automatic incremental syncing** - New RAG entries automatically sync to Pinecone
- **Works with SKIP_EMBEDDING_BOOTSTRAP=true** - Syncs new entries without full recompute
- **Better detection** - Compares entry IDs instead of just counts
- **Non-blocking sync** - All Pinecone operations run in background

## 📝 How to Use
- **Manual sync**: Use `/reload` command in Discord (Admin only)
- **Auto sync**: Happens automatically every 6 hours or when new entries detected
- **Disable embeddings**: Set `FORCE_KEYWORD_SEARCH=true` in Railway to save CPU
- **Memory issues**: Already optimized - caches auto-cleanup, content truncated

## ✅ Status
- ✅ Bot commands working
- ✅ Forum posts responding
- ✅ Pinecone syncing automatically
- ✅ Memory optimized
- ✅ CPU optimized
