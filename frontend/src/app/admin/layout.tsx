import { AdminFrame } from "@/features/admin/admin-frame";
export default function Layout({ children }: { children: React.ReactNode }) {
  return <AdminFrame>{children}</AdminFrame>;
}
