"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { api } from "@/services/api";
import { ErrorNotice } from "@/components/feedback";

function Content() {
  const { user } = useAuth();
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    api<{ name: string | null; learning_goal: string | null }>(
      "/account/profile",
    )
      .then((p) => {
        setName(p.name || "");
        setGoal(p.learning_goal || "");
      })
      .catch(() => {});
  }, []);
  async function save() {
    try {
      await api("/account/profile", {
        method: "PATCH",
        body: JSON.stringify({ name, learning_goal: goal }),
      });
      setMessage("Đã lưu hồ sơ.");
    } catch (e) {
      setMessage((e as Error).message);
    }
  }
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <p className="eyebrow">Tài khoản</p>
        <h1 className="mt-2 text-3xl font-bold">Hồ sơ của bạn</h1>
      </div>
      <div className="panel space-y-5 p-6">
        <p className="text-sm text-stone-600">
          Email: <strong>{user?.email}</strong>
        </p>
        <label className="block text-sm font-semibold">
          Tên hiển thị
          <input
            className="mt-2 w-full rounded-xl border border-stone-300 p-3"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={160}
          />
        </label>
        <label className="block text-sm font-semibold">
          Mục tiêu học tập
          <input
            className="mt-2 w-full rounded-xl border border-stone-300 p-3"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            maxLength={240}
          />
        </label>
        {message && <ErrorNotice message={message} />}
        <button
          onClick={save}
          className="rounded-xl bg-teal-800 px-5 py-3 text-sm font-semibold text-white"
        >
          Lưu hồ sơ
        </button>
      </div>
      <div className="flex gap-5 text-sm font-semibold text-teal-800">
        <Link href="/account/subscription">Gói và thanh toán →</Link>
        <Link href="/settings">Cài đặt luyện tập →</Link>
      </div>
    </div>
  );
}
export default function AccountPage() {
  return (
    <RequireAuth>
      <Content />
    </RequireAuth>
  );
}
