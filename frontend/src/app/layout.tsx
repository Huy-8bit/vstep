import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import { AuthProvider } from "@/features/auth/auth-provider";
import { Shell } from "@/components/shell";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-jakarta",
  display: "swap",
});

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
    <html lang="vi" className={jakarta.variable}>
      <body>
        <AuthProvider>
          <Shell>{children}</Shell>
        </AuthProvider>
        <Toaster />
      </body>
    </html>
  );
}
