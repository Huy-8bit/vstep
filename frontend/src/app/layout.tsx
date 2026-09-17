import type { Metadata } from "next";
import { AuthProvider } from "@/features/auth/auth-provider";
import { Shell } from "@/components/shell";
import "./globals.css";
export const metadata: Metadata = {
  title: {
    default: "VSTEP Writing Lab — Luyện viết, tiến bộ mỗi ngày",
    template: "%s | VSTEP Writing Lab",
  },
  description:
    "Luyện VSTEP Writing với đề thư, bài luận, thi thử 60 phút và nhận phản hồi AI bằng tiếng Việt.",
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
