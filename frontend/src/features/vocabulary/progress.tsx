"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ErrorNotice } from "@/components/feedback";
import { api } from "@/services/api";
import { topicLabels as topics } from "./types";
import { issueLabels, type VocabularyProgress } from "./types";

export function VocabularyProgressPanel({
  data,
}: {
  data?: VocabularyProgress;
}) {
  const [loaded, setLoaded] = useState<VocabularyProgress | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (data) return;
    let active = true;
    api<VocabularyProgress>("/vocabulary/progress")
      .then((r) => {
        if (active) setLoaded(r);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [data]);
  const summary = data || loaded;
  return (
    <section className="panel space-y-5 p-6">
      <div className="flex flex-wrap justify-between gap-3">
        <div>
          <p className="eyebrow">Writing · Speaking · Reading</p>
          <h2 className="mt-2 text-xl font-bold">Vốn từ chủ động của bạn</h2>
        </div>
        <Link
          href="/vocabulary"
          className="text-sm font-semibold text-teal-700"
        >
          Mở sổ từ vựng →
        </Link>
      </div>
      {error && <ErrorNotice message={error} />}
      {summary ? (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              ["Đã lưu", summary.total],
              ["Đã luyện", summary.learned],
              ["Đã nhớ", summary.mastered],
              ["Đến hạn ôn", summary.due],
            ].map(([label, count]) => (
              <div key={label} className="rounded-xl bg-stone-50 p-4">
                <p className="text-xs text-stone-500">{label}</p>
                <p className="mt-2 text-2xl font-bold">{count}</p>
              </div>
            ))}
          </div>
          {!!summary.issue_trends.length && (
            <div className="grid gap-3 sm:grid-cols-2">
              {summary.issue_trends.map((t) => (
                <div
                  key={t.issue_type}
                  className="rounded-xl border border-stone-100 p-4 text-sm"
                >
                  <p className="font-semibold">
                    {issueLabels[t.issue_type] || t.issue_type} ·{" "}
                    {t.trend === "improving"
                      ? "Đang tiến bộ"
                      : t.trend === "needs_practice"
                        ? "Cần luyện thêm"
                        : "Ổn định"}
                  </p>
                  <p className="mt-1 text-xs text-stone-500">
                    {t.recent_accuracy}% đúng trong tối đa 5 lượt gần nhất ·{" "}
                    {t.reviews} lượt đã chấm
                  </p>
                </div>
              ))}
            </div>
          )}
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <h3 className="mb-2 text-sm font-semibold">
                Lỗi dùng từ lặp lại trong bài luyện
              </h3>
              {summary.recurring_errors
                .filter((e) => e.count >= 2)
                .slice(0, 4)
                .map((e) => (
                  <p
                    key={`${e.issue_type}:${e.original}`}
                    className="text-sm leading-7"
                  >
                    <span lang="en">{e.original}</span> ·{" "}
                    {issueLabels[e.issue_type]} · {e.count} bài
                  </p>
                ))}
              {!summary.recurring_errors.some((e) => e.count >= 2) && (
                <p className="text-xs text-stone-500">
                  Chưa có mẫu lỗi lặp lại đủ bằng chứng.
                </p>
              )}
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold">
                Chủ đề ôn nhiều nhất
              </h3>
              {summary.most_practiced_topics.length ? (
                summary.most_practiced_topics.map((t) => (
                  <p key={t.topic} className="text-sm leading-7">
                    {topics[t.topic] || t.topic} · {t.count} lượt
                  </p>
                ))
              ) : (
                <p className="text-xs text-stone-500">
                  Bắt đầu một lượt ôn để ghi nhận tiến độ.
                </p>
              )}
            </div>
          </div>
          <p className="text-xs leading-6 text-stone-500">
            Mức ghi nhớ dựa trên các lượt ôn đến hạn. Đây là lịch học của ứng
            dụng, không phải thang đánh giá VSTEP.
          </p>
        </>
      ) : (
        !error && (
          <p className="text-sm text-stone-500">Đang tải tiến độ từ vựng...</p>
        )
      )}
    </section>
  );
}
