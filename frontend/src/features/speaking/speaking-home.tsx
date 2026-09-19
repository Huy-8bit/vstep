"use client";
import { LearningEntry } from "@/features/learning/integration";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, AudioLines, Clock3, Mic, Sparkles } from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { api, post } from "@/services/api";
import { TEST_PROFILE } from "@/lib/test-profile";
import {
  modes,
  topics,
  type SpeakingMode,
  type SpeakingQuestion,
  type SpeakingSession,
} from "./types";

export function SpeakingHome({
  initialMode = "FULL_TEST",
}: {
  initialMode?: SpeakingMode;
}) {
  return (
    <RequireAuth>
      <SpeakingSetup initialMode={initialMode} />
    </RequireAuth>
  );
}
function SpeakingSetup({ initialMode }: { initialMode: SpeakingMode }) {
  const router = useRouter();
  const [mode, setMode] = useState<SpeakingMode>(initialMode);
  const [source, setSource] = useState("BANK");
  const [topic, setTopic] = useState("random");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<SpeakingQuestion | null>(null);
  const [configured, setConfigured] = useState<boolean | null>(null);
  useEffect(() => {
    api<{ ai_configured: boolean }>("/speaking/config")
      .then((data) => setConfigured(data.ai_configured))
      .catch(() => {});
  }, []);
  async function generate() {
    setBusy("preview");
    setError("");
    try {
      setPreview(
        await post<SpeakingQuestion>("/speaking/questions/generate", {
          part: mode === "PART2" ? 2 : mode === "PART3" ? 3 : 1,
          source,
          topic,
          test_profile: TEST_PROFILE,
          recent_question_ids: preview ? [preview.id] : [],
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function start() {
    setBusy("start");
    setError("");
    try {
      const session = await post<SpeakingSession>("/speaking/sessions", {
        mode,
        source,
        topic,
        test_profile: TEST_PROFILE,
        question_id: mode !== "FULL_TEST" ? preview?.id : undefined,
      });
      router.push(`/speaking/exam/${session.id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy("");
    }
  }
  return (
    <div className="space-y-8">
<LearningEntry skill="Speaking" />
      <div className="panel flex flex-wrap items-center justify-between gap-4 p-5">
        <div>
          <h2 className="font-semibold">Luyện phát âm từng từ, từng câu</h2>
          <p className="mt-1 text-sm text-stone-500">
            Nghe mẫu, thu âm và theo dõi tiến bộ.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/speaking/pronunciation">Mở phòng luyện phát âm</Link>
        </Button>
      </div>
      <section className="relative overflow-hidden rounded-3xl bg-[#e8f0eb] p-7 sm:p-10">
        <div className="relative z-10 max-w-2xl">
          <p className="eyebrow">VSTEP.3–5 · Speaking</p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
            Nói nhiều hơn.
            <br />
            <span className="text-teal-800">Tự tin từng câu.</span>
          </h1>
          <p className="mt-5 max-w-xl text-sm leading-7 text-stone-600">
            Luyện nói với giám khảo AI, nghe lại giọng của bạn và nhận hướng dẫn
            sửa từng câu. Bắt đầu với một câu hỏi, hoặc thử sức cùng bài thi ba
            phần.
          </p>
          <div className="mt-6 flex flex-wrap gap-5 text-xs font-medium text-teal-900">
            <span className="flex items-center gap-2">
              <Mic size={15} /> Trả lời bằng giọng nói
            </span>
            <span className="flex items-center gap-2">
              <Sparkles size={15} /> Phản hồi bằng tiếng Việt
            </span>
          </div>
        </div>
        <AudioLines
          className="absolute -right-8 bottom-0 hidden size-72 rotate-12 text-teal-800/10 sm:block"
          strokeWidth={1}
        />
      </section>
      <div>
        <p className="eyebrow">Chọn một nhịp luyện tập</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {Object.entries(modes).map(([key, item]) => (
            <button
              key={key}
              onClick={() => {
                setMode(key as SpeakingMode);
                setPreview(null);
                setError("");
              }}
              aria-pressed={mode === key}
              disabled={!!busy}
              className={`rounded-2xl border p-5 text-left transition ${mode === key ? "border-teal-800 bg-teal-800 text-white shadow-sm" : "border-stone-200 bg-white hover:border-teal-400"}`}
            >
              <p className="font-semibold">{item.title}</p>
              <p
                className={`mt-2 text-xs ${mode === key ? "text-teal-100" : "text-stone-500"}`}
              >
                {item.subtitle}
              </p>
              <p
                className={`mt-5 flex items-center gap-1.5 text-xs ${mode === key ? "text-teal-100" : "text-stone-400"}`}
              >
                <Clock3 size={13} />
                {item.time}
              </p>
            </button>
          ))}
        </div>
      </div>
      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div className="panel p-6 sm:p-8">
          <h2 className="text-xl font-bold">{modes[mode].title}</h2>
          <p className="mt-2 text-sm leading-6 text-stone-500">
            {modes[mode].description}
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <label className="space-y-2 text-xs font-semibold">
              Nguồn đề
              <select
                className="field mt-2"
                value={source}
                disabled={!!busy}
                onChange={(e) => {
                  setSource(e.target.value);
                  setPreview(null);
                }}
              >
                <option value="BANK">Ngân hàng đề đã kiểm tra</option>
                <option value="AI">Sinh đề với AI</option>
              </select>
            </label>
            <label className="space-y-2 text-xs font-semibold">
              Chủ đề
              <select
                className="field mt-2"
                value={topic}
                disabled={!!busy}
                onChange={(e) => {
                  setTopic(e.target.value);
                  setPreview(null);
                }}
              >
                {Object.entries(topics).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {source === "BANK" && (
            <p className="mt-3 text-xs leading-5 text-stone-500">
              45 đề mẫu VSTEP.3–5. Chọn chủ đề ngẫu nhiên để dùng toàn bộ ngân
              hàng đề.
            </p>
          )}
          {configured === false && (
            <p className="mt-5 rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-900">
              Bạn vẫn có thể luyện với đề mẫu, ghi âm và nghe lại. Chuyển giọng
              nói và chấm bài cần cấu hình OpenAI trên máy chủ.
            </p>
          )}
          {error && <ErrorNotice message={error} />}
          <div className="mt-6 flex flex-wrap gap-3">
            <Button disabled={!!busy} onClick={start}>
              {busy === "start" ? "Đang chuẩn bị đề..." : "Bắt đầu luyện nói"}
              <ArrowRight />
            </Button>
            {mode !== "FULL_TEST" && (
              <Button variant="outline" disabled={!!busy} onClick={generate}>
                {busy === "preview"
                  ? "Đang chuẩn bị..."
                  : preview
                    ? "Đổi đề xem trước"
                    : "Xem trước đề"}
              </Button>
            )}
          </div>
          {preview && (
            <div className="mt-6 space-y-4 rounded-xl border border-stone-200 bg-stone-50 p-5 text-sm leading-7">
              <p className="eyebrow">Đề luyện · Part {preview.part}</p>
              <p>{preview.situation || preview.question_text}</p>
              {preview.topic_sets.map((set) => (
                <div key={set.topic}>
                  <p className="font-semibold">{set.topic}</p>
                  <ul className="ml-5 list-disc">
                    {set.questions.map((q) => (
                      <li key={q}>{q}</li>
                    ))}
                  </ul>
                </div>
              ))}
              {[...preview.options, ...preview.suggested_ideas].map(
                (text, index) => (
                  <p key={text}>
                    {index + 1}. {text}
                  </p>
                ),
              )}
              {preview.part === 3 && (
                <p className="text-stone-500">
                  Bạn có thể thêm ý riêng. Follow-up sẽ xuất hiện sau bài nói
                  chính.
                </p>
              )}
              {preview.part === 1 && (
                <p className="text-stone-500">
                  Hệ thống chọn một câu trong bộ đề này cho lượt luyện.
                </p>
              )}
            </div>
          )}
        </div>
        <aside className="panel p-6 sm:p-8">
          <p className="eyebrow">Một bài thi, ba phần</p>
          <ol className="mt-5 space-y-5">
            {[
              [
                "01",
                "Social Interaction",
                "Hai chủ đề quen thuộc · 3–6 câu hỏi",
              ],
              ["02", "Solution Discussion", "Một tình huống · Ba phương án"],
              ["03", "Topic Development", "Ba ý gợi ý · Ý riêng · Follow-up"],
            ].map(([number, title, desc]) => (
              <li key={number} className="flex gap-4">
                <span className="text-sm font-bold text-teal-700">
                  {number}
                </span>
                <div>
                  <h3 className="text-sm font-semibold">{title}</h3>
                  <p className="mt-1 text-xs leading-5 text-stone-500">
                    {desc}
                  </p>
                </div>
              </li>
            ))}
          </ol>
          <p className="mt-7 border-t border-stone-100 pt-5 text-xs leading-6 text-stone-500">
            Chuẩn bị microphone ở nơi yên tĩnh. Trong thi thử, mỗi câu chỉ ghi
            một lần; phản hồi được mở sau khi kết thúc bài.
          </p>
          <div className="mt-5 flex gap-5 text-sm font-semibold text-teal-800">
            <Link href="/speaking/history">Lịch sử nói →</Link>
            <Link href="/speaking/progress">Tiến độ →</Link>
          </div>
        </aside>
      </section>
    </div>
  );
}
