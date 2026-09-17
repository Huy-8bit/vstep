"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
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
  logout: () => Promise<void>;
}>({ user: null, loading: true, setUser: () => {}, logout: async () => {} });
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);
  const logout = useCallback(async () => {
    await post("/auth/logout");
    setUser(null);
  }, []);
  return (
    <AuthContext.Provider value={{ user, loading, setUser, logout }}>
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
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [user, loading, pathname, router]);
  return loading || !user ? (
    <Loading text="Đang mở không gian luyện tập..." />
  ) : (
    children
  );
}
