/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_DISABLE_MOCK_FALLBACK?: string;
  readonly VITE_USE_MOCK_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface Window {
  api?: {
    ping: () => string;
    chooseDirectory?: () => Promise<string | null>;
    openPath?: (targetPath: string) => Promise<string>;
    showItemInFolder?: (targetPath: string) => Promise<boolean>;
  };
}
