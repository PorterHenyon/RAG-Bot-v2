/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly API_KEY?: string;
  readonly VITE_DISCORD_CLIENT_ID?: string;
  readonly VITE_DISCORD_REDIRECT_URI?: string;
  readonly VITE_GEMINI_API_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

