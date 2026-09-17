"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  BookOpenText,
  Check,
  Clock3,
  Sparkles,
} from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { api, post } from "@/services/api";
import { TEST_PROFILE } from "@/lib/test-profile";
import {
  modes,
  questionTypes,
  topics,
  type Bank,
  type ReadingMode,
  type ReadingPassage,
  type ReadingProgress,
  type ReadingSession,
} from "./types";
export function ReadingHome({
  initialMode = "FULL_TEST",
  initialType = "inference",
}: {
  initialMode?: ReadingMode;
  initialType?: string;
}) {
  return (
    <RequireAuth>
      <Setup initialMode={initialMode} initialType={initialType} />
    </RequireAuth>
  );
}
function Setup({
  initialMode,
  initialType,
}: {
  initialMode: ReadingMode;
  initialType: string;
}) {
  const router = useRouter();
  const [mode, setMode] = useState<ReadingMode>(initialMode);
  const [topic, setTopic] = useState("random");
  const [target, setTarget] = useState(initialType);
  const [timed, setTimed] = useState(false);
  const [bank, setBank] = useState<Bank | null>(null);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const bankRequest = useRef(0);
  const [recommendation, setRecommendation] = useState<
    ReadingProgress["weaknesses"][number] | null
  >(null);
  const loadBank = useCallback(async () => {
    const request = ++bankRequest.current;
    const data = await api<Bank>(`/reading/bank?topic=${topic}`);
    if (request === bankRequest.current) setBank(data);
    return data;
  }, [topic]);
  useEffect(() => {
    setBank(null);
    setSelected("");
    setError("");
    loadBank().catch((e) => setError(e.message));
  }, [loadBank]);
  useEffect(() => {
    api<ReadingProgress>("/reading/progress")
      .then((data) => setRecommendation(data.weaknesses[0] || null))
      .catch(() => {});
  }, []);
  const count =
    mode === "QUICK_PRACTICE" || mode === "QUESTION_TYPE_PRACTICE" ? 5 : 10;
  const eligible =
    bank?.items.filter((p) =>
      mode === "QUESTION_TYPE_PRACTICE"
        ? p.question_types.includes(target)
        : p.question_count >= count,
    ) || [];
  async function generate() {
    setError("");
    setBusy("Đang tạo bài đọc và kiểm tra câu hỏi...");
    try {
      const p = await post<ReadingPassage>("/reading/questions/generate", {
        mode,
        test_profile: TEST_PROFILE,
        topic,
        question_count: count,
        target_question_types:
          mode === "QUESTION_TYPE_PRACTICE" ? [target] : [],
        recent_titles: bank?.items.slice(-20).map((p) => p.title) || [],
      });
      await loadBank();
      if (mode !== "FULL_TEST") setSelected(p.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function start() {
    setError("");
    setBusy("Đang chuẩn bị phiên Reading...");
    try {
      const needed = mode === "FULL_TEST" ? 4 : 1;
      const missing =
        mode === "FULL_TEST"
          ? (bank?.full_test_missing_passages ?? 4)
          : Math.max(0, needed - eligible.length);
      if (missing && bank?.ai_configured && !selected) {
        for (let i = 0; i < missing; i++) {
          setBusy(`Đang bổ sung bài đọc ${i + 1}/${missing}...`);
          await post("/reading/questions/generate", {
            mode,
            test_profile: TEST_PROFILE,
            topic,
            question_count: count,
            target_question_types:
              mode === "QUESTION_TYPE_PRACTICE" ? [target] : [],
          });
          const updated = await loadBank();
          if (mode === "FULL_TEST" && updated.full_test_missing_passages === 0)
            break;
        }
        await loadBank();
      }
      const s = await post<ReadingSession>("/reading/sessions", {
        mode,
        test_profile: TEST_PROFILE,
        topic,
        timed,
        target_question_type: mode === "QUESTION_TYPE_PRACTICE" ? target : null,
        passage_id: mode === "FULL_TEST" ? null : selected || null,
      });
      router.push(`/reading/exam/${s.id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy("");
    }
  }
  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-3xl bg-[#eaf0e6] p-7 sm:p-10">
        <div className="relative z-10 max-w-2xl">
          <p className="eyebrow">VSTEP.3–5 · Reading</p>
          <h1 className="mt-4 text-4xl font-bold leading-tight tracking-tight sm:text-5xl">
            Đọc sâu hơn.
            <br />
            <span className="text-teal-800">Hiểu rõ từng lựa chọn.</span>
          </h1>
          <p className="mt-5 max-w-xl text-sm leading-7 text-stone-600">
            Luyện đọc hiểu với bài đọc tiếng Anh, trắc nghiệm A/B/C/D và bằng
            chứng rõ ràng cho từng đáp án. Tìm ra cách đọc phù hợp với bạn.
          </p>
          <div className="mt-6 flex flex-wrap gap-5 text-xs font-medium text-teal-900">
            <span className="flex items-center gap-2">
              <Clock3 size={15} /> 4 passages · 40 câu · 60 phút
            </span>
            <span className="flex items-center gap-2">
              <Check size={15} /> Có điểm ngay sau khi nộp
            </span>
          </div>
        </div>
        <BookOpenText
          className="absolute -right-8 bottom-0 hidden size-72 rotate-12 text-teal-900/10 sm:block"
          strokeWidth={1}
        />
      </section>
      {recommendation && (
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-teal-100 bg-teal-50 p-5">
          <p className="text-sm leading-6 text-teal-900">
            Bạn đang đúng {recommendation.correct}/{recommendation.total} câu{" "}
            {questionTypes[recommendation.key]} ({recommendation.accuracy}%).
            Hôm nay, thử tập trung vào dạng này.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setMode("QUESTION_TYPE_PRACTICE");
              setTarget(recommendation.key);
              setSelected("");
            }}
          >
            Luyện ngay →
          </Button>
        </div>
      )}
      <section>
        <p className="eyebrow mb-4">Chọn cách luyện đọc</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(modes).map(([key, item]) => (
            <button
              key={key}
              disabled={!!busy}
              aria-pressed={mode === key}
              onClick={() => {
                setMode(key as ReadingMode);
                setSelected("");
                setError("");
              }}
              className={`rounded-2xl border p-5 text-left ${mode === key ? "border-teal-800 bg-teal-800 text-white" : "border-stone-200 bg-white hover:border-teal-400"}`}
            >
              <h2 className="font-bold">{item.title}</h2>
              <p
                className={`mt-3 text-xs leading-6 ${mode === key ? "text-teal-100" : "text-stone-500"}`}
              >
                {item.meta}
              </p>
            </button>
          ))}
        </div>
      </section>
      <section className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <div className="panel p-6 sm:p-8">
          <h2 className="text-xl font-bold">{modes[mode].title}</h2>
          <p className="mt-3 text-xs font-medium text-teal-800">
            VSTEP.3–5 · Một bài thi đánh giá nhiều bậc năng lực
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-500">
            {modes[mode].description}
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <label className="text-xs font-semibold">
              Luyện theo chủ đề
              <select
                className="field mt-2"
                disabled={!!busy}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
              >
                {Object.entries(topics).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            {mode === "QUESTION_TYPE_PRACTICE" && (
              <label className="text-xs font-semibold sm:col-span-2">
                Dạng câu hỏi
                <select
                  className="field mt-2"
                  disabled={!!busy}
                  value={target}
                  onChange={(e) => {
                    setTarget(e.target.value);
                    setSelected("");
                  }}
                >
                  {Object.entries(questionTypes).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {mode !== "FULL_TEST" && (
              <label className="text-xs font-semibold sm:col-span-2">
                Bài đọc
                <select
                  className="field mt-2"
                  value={selected}
                  disabled={!!busy || !bank}
                  onChange={(e) => setSelected(e.target.value)}
                >
                  <option value="">Tự chọn · Ưu tiên bài chưa làm</option>
                  {eligible.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.title} · {p.word_count} từ
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          {mode !== "FULL_TEST" && (
            <label className="mt-5 flex items-center gap-3 text-sm">
              <input
                type="checkbox"
                checked={timed}
                disabled={!!busy}
                onChange={(e) => setTimed(e.target.checked)}
                className="size-4 accent-teal-800"
              />
              Bật đồng hồ {mode === "PASSAGE_PRACTICE" ? "15" : "8"} phút
            </label>
          )}
          <p className="mt-5 text-xs leading-6 text-stone-500">
            {bank
              ? `${eligible.length} bài đọc phù hợp trong ngân hàng. ${mode === "QUESTION_TYPE_PRACTICE" ? "Số câu thực tế theo các câu cùng dạng hiện có, tối đa 5 câu." : "Đề có sẵn được dùng lại, ưu tiên bài bạn chưa làm."}`
              : "Đang tải ngân hàng đề..."}
          </p>
          {bank &&
            mode === "FULL_TEST" &&
            bank.full_test_missing_passages > 0 && (
              <p className="mt-3 text-xs leading-6 text-stone-500">
                Cần bổ sung {bank.full_test_missing_passages} bài đọc để bộ lọc
                này đủ cấu trúc thi thử và độ phủ dạng câu. Chọn chủ đề ngẫu
                nhiên để dùng ngân hàng mẫu đầy đủ.
              </p>
            )}
          {bank && !bank.ai_configured && (
            <p className="mt-3 rounded-xl bg-stone-50 p-4 text-xs leading-6 text-stone-600">
              Đề mẫu, chấm điểm và giải thích đáp án hoạt động ngay. Tạo đề mới
              hoặc tra từ vựng bằng AI cần cấu hình OpenAI. Thi thử từ ngân hàng
              mẫu có đủ cấu trúc VSTEP.3–5 khi chọn chủ đề ngẫu nhiên.
            </p>
          )}
          {error && <ErrorNotice message={error} />}
          {busy && (
            <p role="status" className="mt-4 text-sm text-teal-700">
              {busy}
            </p>
          )}
          <div className="mt-6 flex flex-wrap gap-3">
            <Button disabled={!!busy || !bank} onClick={start}>
              Bắt đầu đọc
              <ArrowRight />
            </Button>
            <Button
              variant="outline"
              disabled={!!busy || !bank}
              onClick={generate}
            >
              <Sparkles />
              Tạo đề mới bằng AI
            </Button>
          </div>
        </div>
        <aside className="panel p-7">
          <p className="eyebrow">Đọc · Chọn · Hiểu</p>
          <ol className="mt-5 space-y-5">
            {[
              [
                "01",
                "Tìm ý trong bài",
                "Bài đọc và câu hỏi ở hai khung cuộn riêng; chuyển câu bằng navigator.",
              ],
              [
                "02",
                "Chủ động phân bổ thời gian",
                "Đánh dấu câu chưa chắc chắn rồi quay lại. Đáp án được lưu tự động.",
              ],
              [
                "03",
                "Học từ cả đáp án sai",
                "Xem giải thích từng phương án, đoạn bằng chứng và dạng câu cần luyện thêm.",
              ],
            ].map(([number, title, text]) => (
              <li key={number} className="flex gap-4">
                <span className="text-sm font-bold text-teal-700">
                  {number}
                </span>
                <div>
                  <h3 className="text-sm font-semibold">{title}</h3>
                  <p className="mt-2 text-xs leading-6 text-stone-500">
                    {text}
                  </p>
                </div>
              </li>
            ))}
          </ol>
          <div className="mt-6 flex gap-5 border-t border-stone-100 pt-5 text-sm font-semibold text-teal-800">
            <Link href="/reading/history">Lịch sử →</Link>
            <Link href="/reading/progress">Tiến độ →</Link>
          </div>
        </aside>
      </section>
    </div>
  );
}
