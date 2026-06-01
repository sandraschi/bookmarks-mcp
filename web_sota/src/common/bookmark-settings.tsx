import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { BrowserName } from "@/common/bookmark-types";

const STORAGE_KEY = "bookmarks-browser-settings";

export interface BookmarkSettings {
  browser: BrowserName;
  profileName: string;
  forceAccess: boolean;
}

interface BookmarkSettingsContextValue extends BookmarkSettings {
  setBrowser: (browser: BrowserName) => void;
  setProfileName: (profile: string) => void;
  setForceAccess: (force: boolean) => void;
  callOptions: {
    browser: BrowserName;
    profileName?: string;
    forceAccess?: boolean;
  };
}

const defaults: BookmarkSettings = {
  browser: "firefox",
  profileName: "",
  forceAccess: false,
};

const BookmarkSettingsContext =
  createContext<BookmarkSettingsContextValue | null>(null);

function loadSettings(): BookmarkSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaults;
    return { ...defaults, ...JSON.parse(raw) };
  } catch {
    return defaults;
  }
}

export function BookmarkSettingsProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [settings, setSettings] = useState<BookmarkSettings>(loadSettings);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  const setBrowser = useCallback((browser: BrowserName) => {
    setSettings((prev) => ({ ...prev, browser }));
  }, []);

  const setProfileName = useCallback((profileName: string) => {
    setSettings((prev) => ({ ...prev, profileName }));
  }, []);

  const setForceAccess = useCallback((forceAccess: boolean) => {
    setSettings((prev) => ({ ...prev, forceAccess }));
  }, []);

  const callOptions = useMemo(
    () => ({
      browser: settings.browser,
      profileName: settings.profileName || undefined,
      forceAccess: settings.forceAccess,
    }),
    [settings],
  );

  const value = useMemo(
    () => ({
      ...settings,
      setBrowser,
      setProfileName,
      setForceAccess,
      callOptions,
    }),
    [settings, setBrowser, setProfileName, setForceAccess, callOptions],
  );

  return (
    <BookmarkSettingsContext.Provider value={value}>
      {children}
    </BookmarkSettingsContext.Provider>
  );
}

export function useBookmarkSettings(): BookmarkSettingsContextValue {
  const ctx = useContext(BookmarkSettingsContext);
  if (!ctx) {
    throw new Error(
      "useBookmarkSettings must be used within BookmarkSettingsProvider",
    );
  }
  return ctx;
}
