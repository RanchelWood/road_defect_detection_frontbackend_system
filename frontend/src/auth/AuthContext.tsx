import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { refresh as refreshRequest } from "../api/auth";
import type { AuthPayload, UserPublic } from "../types";

type AuthState = {
  accessToken: string;
  refreshToken: string;
  user: UserPublic;
};

type AuthContextValue = {
  authState: AuthState | null;
  setAuthFromPayload: (payload: AuthPayload) => void;
  clearAuth: () => void;
  refreshSession: () => Promise<void>;
};

const STORAGE_KEY = "road_defect_auth";

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function parseStoredState(raw: string | null): AuthState | null {
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AuthState;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authState, setAuthState] = useState<AuthState | null>(() => parseStoredState(localStorage.getItem(STORAGE_KEY)));

  useEffect(() => {
    if (authState) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(authState));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [authState]);

  const setAuthFromPayload = useCallback((payload: AuthPayload) => {
    setAuthState({
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token,
      user: payload.user,
    });
  }, []);

  const clearAuth = useCallback(() => {
    setAuthState(null);
  }, []);

  const refreshSession = useCallback(async () => {
    if (!authState?.refreshToken) {
      return;
    }

    const payload = await refreshRequest(authState.refreshToken);
    setAuthFromPayload(payload);
  }, [authState?.refreshToken, setAuthFromPayload]);

  const value = useMemo<AuthContextValue>(
    () => ({
      authState,
      setAuthFromPayload,
      clearAuth,
      refreshSession,
    }),
    [authState, clearAuth, refreshSession, setAuthFromPayload],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}