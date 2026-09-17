"use client";
import { RequireAuth } from "@/features/auth/auth-provider";
import { PracticeCards } from "@/features/writing/practice-cards";
import { FullTestStart } from "@/features/writing/practice-setup";
export default function Practice() {
  return (
    <RequireAuth>
      <p className="eyebrow">Không gian luyện tập</p>
      <h1 className="mb-3 mt-3 text-3xl font-bold">
        Dành thời gian cho bài viết của bạn
      </h1>
      <p className="mb-8 text-sm text-stone-500">
        Chọn luyện từng kỹ năng hoặc thử sức với bài thi Writing đầy đủ.
      </p>
      <PracticeCards />
      <FullTestStart />
    </RequireAuth>
  );
}
