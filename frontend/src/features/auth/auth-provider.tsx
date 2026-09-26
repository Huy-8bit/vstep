"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, post } from "@/services/api";
import type { User } from "@/types";
import { Loading } from "@/components/feedback";

const AuthContext = createContext<{
  user: User | null;
  loading: boolean;
  setUser: (user: User | null) => void;
  refreshUser: () => Promise<User | null>;
  logout: () => Promise<void>;
}>({
  user: null,
  loading: true,
  setUser: () => {},
  refreshUser: async () => null,
  logout: async () => {},
});
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const authVersion = useRef(0);
  const pathname = usePathname();
  const updateUser = useCallback((current: User | null) => {
    authVersion.current += 1;
    setUser(current);
    setLoading(false);
  }, []);
  const refreshUser = useCallback(async () => {
    try {
      const current = await api<User>("/auth/me");
      updateUser(current);
      return current;
    } catch {
      updateUser(null);
      return null;
    }
  }, [updateUser]);
  useEffect(() => {
    let active = true;
    const version = authVersion.current;
    api<User>("/auth/me")
      .then((current) => {
        if (active && version === authVersion.current) setUser(current);
      })
      .catch(() => {
        if (active && version === authVersion.current) setUser(null);
      })
      .finally(() => {
        if (active && version === authVersion.current) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [pathname]);
  const logout = useCallback(async () => {
    await post("/auth/logout");
    updateUser(null);
  }, [updateUser]);
  return (
    <AuthContext.Provider
      value={{ user, loading, setUser: updateUser, refreshUser, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => useContext(AuthContext);
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (!loading && !user)
      router.replace(
        `/login?next=${encodeURIComponent(pathname + window.location.search)}`,
      );
  }, [user, loading, pathname, router]);
  return loading || !user ? (
    <Loading text="Đang mở không gian luyện tập..." />
  ) : (
    children
  );
}
