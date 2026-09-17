"use client";
import { useCallback, useEffect, useState } from "react";
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
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { api } from "@/services/api";
import { SkillSwitch } from "./skill-switch";
import {
  criterionLabels,
  disclaimer,
  modes,
  scoreText,
  type Criterion,
  type SpeakingMode,
} from "./types";
type Progress = {
  graded_sessions: number;
  complete_scores: number;
  average: Record<Criterion | "overall", number | null>;
  criterion_counts: Record<Criterion | "overall", number>;
  full_test_average: number | null;
  timeline: (Record<Criterion | "overall", number | null> & {
    id: string;
    date: string;
    mode: SpeakingMode;
  })[];
  weaknesses: { category: string; subtype: string; count: number }[];
};
const colors = {
  overall: "#115e59",
  grammar: "#0284c7",
  vocabulary: "#7c3aed",
  pronunciation: "#c2410c",
  fluency: "#be185d",
  structures: "#65a30d",
};
const labels: Record<string, string> = {
  grammar: "Ngữ pháp",
  vocabulary: "Từ vựng",
  pronunciation: "Phát âm",
  fluency: "Trôi chảy",
  coherence: "Mạch lạc",
  content: "Nội dung",
  task_response: "Đáp ứng đề",
  verb_tense: "Thì động từ",
  tense: "Thì động từ",
  word_stress: "Trọng âm từ",
  long_pause: "Khoảng dừng dài",
  subject_verb_agreement: "Hòa hợp chủ ngữ – động từ",
  article: "Mạo từ",
  final_sound: "Âm cuối",
  word_choice: "Lựa chọn từ",
  idea_development: "Phát triển ý",
  repetition: "Lặp từ",
};
export function SpeakingProgress() {
  return (
    <RequireAuth>
      <ProgressView />
    </RequireAuth>
  );
}
function ProgressView() {
  const [data, setData] = useState<Progress | null>(null);
  const [mode, setMode] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      setData(await api(`/speaking/progress${mode ? `?mode=${mode}` : ""}`));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [mode]);
  useEffect(() => {
    void load();
  }, [load]);
  return (
    <>
      <SkillSwitch section="progress" active="speaking" />
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Từng câu nói, từng bước tiến</p>
          <h1 className="mt-2 text-3xl font-bold">Tiến độ Speaking</h1>
        </div>
        <label className="text-xs font-semibold">
          Phạm vi thống kê
          <select
            className="field mt-2"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            <option value="">Tất cả lượt luyện</option>
            {Object.entries(modes).map(([value, item]) => (
              <option key={value} value={value}>
                {item.title}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <>
          <ErrorNotice message={error} />
          <Button onClick={load}>Thử lại</Button>
        </>
      )}
      {loading ? (
        <Loading />
      ) : data?.graded_sessions ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <Stat
              label="Điểm Speaking trung bình"
              value={scoreText(data.average.overall)}
              note={`${data.complete_scores} phiên có đủ năm tiêu chí`}
            />
            <Stat
              label="Điểm thi thử trung bình"
              value={scoreText(data.full_test_average)}
              note="Chỉ các bài Full Test đã chấm đủ"
            />
            <Stat
              label="Phiên đã nhận phản hồi"
              value={String(data.graded_sessions)}
              note="Gồm phản hồi đầy đủ và phản hồi một phần"
            />
          </div>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
            {Object.entries(criterionLabels).map(([key, label]) => (
              <Stat
                key={key}
                label={label}
                value={scoreText(data.average[key as Criterion])}
                note={`${data.criterion_counts[key as Criterion]} phiên có dữ liệu`}
              />
            ))}
          </div>
          <section className="panel p-5 sm:p-7">
            <h2 className="text-lg font-bold">Điểm qua các lần luyện</h2>
            <p className="mb-6 mt-2 text-xs leading-6 text-stone-500">
              Chọn một chế độ để so sánh những bài luyện tương đồng. Phần chưa
              đủ dữ liệu không được điền thành điểm 0.
            </p>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={data.timeline.map((item) => ({
                    ...item,
                    label: new Date(item.date).toLocaleDateString("vi-VN"),
                  }))}
                  margin={{ top: 10, right: 20, left: -20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
                  <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 10]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {Object.entries({
                    overall: "Tổng điểm",
                    ...criterionLabels,
                  }).map(([key, label]) => (
                    <Line
                      key={key}
                      dataKey={key}
                      name={label}
                      stroke={colors[key as keyof typeof colors]}
                      strokeWidth={key === "overall" ? 3 : 1.5}
                      dot={{ r: 3 }}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>
          <section className="panel p-6">
            <h2 className="mb-5 text-lg font-bold">
              Những điểm cần luyện thêm
            </h2>
            {data.weaknesses.length ? (
              <div className="grid gap-4 sm:grid-cols-2">
                {data.weaknesses.map((item, index) => (
                  <div
                    key={`${item.category}:${item.subtype}`}
                    className="flex items-center gap-4 rounded-xl bg-stone-50 p-4"
                  >
                    <span className="text-lg font-bold text-teal-700">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-semibold">
                        {labels[item.subtype] ||
                          item.subtype.replaceAll("_", " ")}
                      </p>
                      <p className="mt-1 text-xs text-stone-500">
                        {labels[item.category] || item.category}
                      </p>
                    </div>
                    <span className="text-xs text-stone-500">
                      {item.count} lần
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-500">
                Chưa có lỗi lặp lại được ghi nhận.
              </p>
            )}
          </section>
          <p className="text-xs leading-6 text-stone-500">
            Trung bình mỗi tiêu chí chỉ dùng các phiên có điểm tương ứng. Điểm
            lượt luyện theo Part dùng để theo dõi luyện tập. {disclaimer}
          </p>
        </div>
      ) : (
        !error && (
          <EmptyState
            title="Tiến bộ bắt đầu từ lần nói đầu tiên"
            description="Hoàn thành một lượt Speaking và nhận phản hồi AI để mở biểu đồ cùng các điểm cần cải thiện."
          >
            <Button asChild>
              <Link href="/speaking">Bắt đầu luyện nói</Link>
            </Button>
          </EmptyState>
        )
      )}
    </>
  );
}
function Stat({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="panel p-5">
      <p className="text-xs font-semibold text-stone-500">{label}</p>
      <p className="mt-4 text-3xl font-bold text-teal-800">{value}</p>
      <p className="mt-2 text-xs leading-5 text-stone-400">{note}</p>
    </div>
  );
}
