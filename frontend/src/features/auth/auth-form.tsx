"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, LoaderCircle, PenLine } from "lucide-react";
import { useAuth } from "./auth-provider";
import { post } from "@/services/api";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import type { User } from "@/types";

export function AuthForm({ register = false }: { register?: boolean }) {
  const { setUser } = useAuth();
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const user = await post<User>(
        `/auth/${register ? "register" : "login"}`,
        { email: form.get("email"), password: form.get("password") },
      );
      setUser(user);
      const next =
        new URLSearchParams(window.location.search).get("next") || "/practice";
      router.replace(
        next.startsWith("/") && !next.startsWith("//") && !next.includes("\\")
          ? next
          : "/practice",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="mx-auto grid max-w-5xl overflow-hidden rounded-3xl border border-stone-200 bg-white md:my-8 md:grid-cols-2">
      <div className="bg-teal-900 p-8 text-white sm:p-12">
        <PenLine className="mb-12 size-9 text-teal-200" />
        <p className="mb-4 text-xs font-bold uppercase tracking-[.2em] text-teal-200">
          Không gian luyện viết của bạn
        </p>
        <h1 className="text-3xl font-semibold leading-snug">
          Một thói quen nhỏ.
          <br />
          Một bước tiến mỗi ngày.
        </h1>
        <p className="mt-5 text-sm leading-7 text-teal-100/80">
          Tập trung vào bài viết. Hiểu rõ điểm cần cải thiện. Theo dõi sự tiến
          bộ qua từng lần luyện tập.
        </p>
        <div className="mt-10 space-y-4 text-sm text-teal-50">
          {[
            "Đề luyện tập theo format VSTEP",
            "Tự động lưu bài viết",
            "Phản hồi chi tiết bằng tiếng Việt",
          ].map((t) => (
            <p key={t} className="flex gap-3">
              <Check className="size-4 text-teal-300" />
              {t}
            </p>
          ))}
        </div>
      </div>
      <div className="p-8 sm:p-12">
        <h2 className="text-2xl font-bold">
          {register ? "Bắt đầu hành trình viết" : "Chào mừng bạn trở lại"}
        </h2>
        <p className="mt-3 text-sm text-stone-500">
          {register
            ? "Tạo tài khoản để lưu bài và theo dõi tiến bộ."
            : "Đăng nhập để tiếp tục buổi luyện tập của bạn."}
        </p>
        <form className="mt-8 space-y-5" onSubmit={submit}>
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-semibold">
              Email
            </label>
            <input
              className="field"
              id="email"
              name="email"
              type="email"
              placeholder="ban@example.com"
              autoComplete="email"
              required
              maxLength={320}
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-semibold"
            >
              Mật khẩu
            </label>
            <input
              className="field"
              id="password"
              name="password"
              type="password"
              placeholder="Ít nhất 8 ký tự"
              autoComplete={register ? "new-password" : "current-password"}
              required
              minLength={8}
              maxLength={128}
            />
          </div>
          {error && <ErrorNotice message={error} />}
          <Button disabled={busy} className="w-full" size="lg">
            {busy ? <LoaderCircle className="animate-spin" /> : <ArrowRight />}
            {register ? "Tạo tài khoản" : "Đăng nhập"}
          </Button>
        </form>
        <p className="mt-7 text-center text-sm text-stone-500">
          {register ? "Đã có tài khoản?" : "Chưa có tài khoản?"}{" "}
          <Link
            href={register ? "/login" : "/register"}
            className="font-semibold text-teal-800 underline underline-offset-4"
          >
            {register ? "Đăng nhập" : "Đăng ký"}
          </Link>
        </p>
      </div>
    </div>
  );
}
