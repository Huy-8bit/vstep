import type { Metadata } from "next";
import { AuthProvider } from "@/features/auth/auth-provider";
import { Shell } from "@/components/shell";
import "./globals.css";
export const metadata: Metadata = {
  title: {
    default: "VSTEP Practice Platform — Luyện đọc, viết và nói mỗi ngày",
    template: "%s | VSTEP Practice Platform",
  },
  description:
    "Luyện VSTEP Reading, Writing và Speaking với đề mẫu, thi thử, ghi âm và phản hồi AI bằng tiếng Việt.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>
        <AuthProvider>
          <Shell>{children}</Shell>
        </AuthProvider>
      </body>
    </html>
  );
}
