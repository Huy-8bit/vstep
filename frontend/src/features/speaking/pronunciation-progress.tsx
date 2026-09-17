"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api } from "@/services/api";
import {
  coachLink,
  type PronunciationProgressData,
} from "./pronunciation-types";
import { scoreText } from "./types";

export function PronunciationProgress() {
  const [data, setData] = useState<PronunciationProgressData | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    api<PronunciationProgressData>("/speaking/pronunciation/progress")
      .then((result) => {
        if (active) {
          setData(result);
          setError("");
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [retry]);
  return (
    <section className="panel space-y-6 p-5 sm:p-7">
      <div className="flex flex-wrap justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold">Tiến bộ luyện phát âm</h2>
          <p className="mt-2 text-sm text-stone-500">
            Các lượt đọc mẫu theo từ và câu. So sánh cùng nội dung giúp bạn nhận
            ra thay đổi rõ hơn.
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link href="/speaking/pronunciation">Luyện phát âm</Link>
        </Button>
      </div>
      {error && (
        <>
          <ErrorNotice message={error} />
          <Button
            onClick={() => setRetry((value) => value + 1)}
            variant="outline"
          >
            Tải lại
          </Button>
        </>
      )}
      {!data && !error && <Loading text="Đang tổng hợp lượt luyện..." />}
      {data && !data.attempts && (
        <p className="text-sm text-stone-500">
          Chưa có lượt luyện được phân tích. Bạn có thể bắt đầu từ một từ cần
          chú ý trong kết quả Speaking.
        </p>
      )}
      {data && data.attempts > 0 && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl bg-teal-50 p-4">
              <p className="text-xs text-teal-700">Phát âm trung bình</p>
              <p className="mt-2 text-2xl font-bold text-teal-900">
                {scoreText(data.average_pronunciation)}
              </p>
              <p className="mt-1 text-xs text-teal-700">
                {data.scored_attempts} lượt đủ dữ liệu
              </p>
            </div>
            <div className="rounded-xl bg-stone-50 p-4">
              <p className="text-xs text-stone-500">Lượt đã phân tích</p>
              <p className="mt-2 text-2xl font-bold">{data.attempts}</p>
            </div>
          </div>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data.timeline.map((item, i) => ({
                  ...item,
                  label: `${i + 1}. ${new Date(item.date).toLocaleDateString("vi-VN")}`,
                }))}
                margin={{ top: 8, right: 15, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} />
                <Tooltip
                  labelFormatter={(_, payload) =>
                    payload?.[0]?.payload?.reference_text || "Lượt luyện"
                  }
                />
                <Legend />
                <Line
                  dataKey="pronunciation"
                  name="Phát âm"
                  stroke="#115e59"
                  strokeWidth={2}
                  connectNulls={false}
                />
                <Line
                  dataKey="fluency"
                  name="Trôi chảy"
                  stroke="#be185d"
                  strokeWidth={2}
                  connectNulls={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs leading-6 text-stone-500">
            Đọc một từ có thể chưa đủ để chấm độ trôi chảy. Các mục thiếu điểm
            được giữ trống.
          </p>
          <div className="grid gap-6 md:grid-cols-2">
            {[
              { title: "Từ/câu còn khó", items: data.difficult_words },
              { title: "Từ/câu đã tiến bộ", items: data.improved_words },
            ].map((group) => (
              <div key={group.title}>
                <h3 className="mb-3 font-semibold">{group.title}</h3>
                {!group.items.length && (
                  <p className="text-sm text-stone-500">
                    Chưa đủ lượt luyện để ghi nhận.
                  </p>
                )}
                <div className="space-y-3">
                  {group.items.map((item) => (
                    <Link
                      href={coachLink(item.reference_text)}
                      key={item.reference_hash}
                      className="block rounded-lg bg-stone-50 p-3"
                    >
                      <p
                        lang="en"
                        className="text-sm font-medium text-teal-800"
                      >
                        {item.reference_text}
                      </p>
                      <p className="mt-1 text-xs text-stone-500">
                        {scoreText(item.first_score)} →{" "}
                        {scoreText(item.latest_score)} · {item.attempts} lượt
                      </p>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div>
            <h3 className="mb-3 font-semibold">
              Vấn đề thường gặp trong các lượt luyện
            </h3>
            {data.recurring_issues.length ? (
              <div className="flex flex-wrap gap-2">
                {data.recurring_issues.map((issue, i) => (
                  <Link
                    key={i}
                    href={coachLink(issue.target, undefined, issue.type)}
                    className="rounded-lg border border-stone-200 px-3 py-2 text-sm text-teal-800"
                  >
                    {issue.target} · {issue.count} lần
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-500">
                Chưa có vấn đề đủ độ tin cậy được ghi nhận.
              </p>
            )}
          </div>
        </>
      )}
    </section>
  );
}
