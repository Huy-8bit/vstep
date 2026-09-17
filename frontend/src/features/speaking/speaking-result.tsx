"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  ChevronDown,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorNotice, Loading } from "@/components/feedback";
import { api, post } from "@/services/api";
import { AudioPlayer } from "./audio-player";
import {
  criterionLabels,
  disclaimer,
  duration,
  modes,
  scoreText,
  type Criterion,
  type Improvement,
  type SpeakingAnswer,
  type SpeakingSession,
} from "./types";

export function SpeakingResult({ id }: { id: string }) {
  return (
    <RequireAuth>
      <Result id={id} />
    </RequireAuth>
  );
}
function Result({ id }: { id: string }) {
  const [session, setSession] = useState<SpeakingSession | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [details, setDetails] = useState(false);
  const [selected, setSelected] = useState("all");
  const [tab, setTab] = useState("overview");
  const running = useRef(false);
  const autoStarted = useRef(false);
  const process = useCallback(
    async (initial: SpeakingSession, retryAudio = false) => {
      if (running.current) return;
      running.current = true;
      setError("");
      try {
        const recordings = initial.answers.filter((a) => a.has_audio);
        for (let i = 0; i < recordings.length; i++) {
          const answer = recordings[i];
          setBusy(
            `Đang chuyển giọng nói thành văn bản · ${i + 1}/${recordings.length}`,
          );
          const transcribed = await post<SpeakingAnswer>(
            `/speaking/answers/${answer.id}/transcribe`,
          );
          setSession(
            (s) =>
              s && {
                ...s,
                answers: s.answers.map((a) =>
                  a.id === answer.id ? transcribed : a,
                ),
              },
          );
          setBusy(`Đang xử lý bài nói · ${i + 1}/${recordings.length}`);
          const analyzed = await post<SpeakingAnswer>(
            `/speaking/answers/${answer.id}/analyze${retryAudio ? "?retry=true" : ""}`,
          );
          setSession(
            (s) =>
              s && {
                ...s,
                answers: s.answers.map((a) =>
                  a.id === answer.id ? analyzed : a,
                ),
              },
          );
        }
        setBusy("Đang chấm bài và chuẩn bị hướng dẫn cải thiện...");
        await post(`/speaking/sessions/${id}/grade`);
        setSession(await api<SpeakingSession>(`/speaking/results/${id}`));
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setBusy("");
        running.current = false;
      }
    },
    [id],
  );
  const load = useCallback(async () => {
    setError("");
    try {
      const data = await api<SpeakingSession>(`/speaking/results/${id}`);
      setSession(data);
      if (
        data.status !== "IN_PROGRESS" &&
        !data.grading &&
        data.answers.some((a) => a.has_audio) &&
        !autoStarted.current
      ) {
        autoStarted.current = true;
        void process(data);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }, [id, process]);
  useEffect(() => {
    void load();
  }, [load]);
  if (!session)
    return error ? (
      <>
        <ErrorNotice message={error} />
        <Button onClick={load}>Thử lại</Button>
      </>
    ) : (
      <Loading text="Đang mở kết quả Speaking..." />
    );
  if (session.status === "IN_PROGRESS")
    return (
      <EmptyState
        title="Phiên Speaking chưa kết thúc"
        description="Tiếp tục các câu hỏi còn lại để mở kết quả và phản hồi."
      >
        <Button asChild>
          <Link href={`/speaking/exam/${id}`}>Tiếp tục bài nói</Link>
        </Button>
      </EmptyState>
    );
  const g = session.grading;
  const chosen = session.answers.filter(
    (a) => selected === "all" || String(a.sequence_number) === selected,
  );
  const match = (item: { sequence_number: number }) =>
    selected === "all" || String(item.sequence_number) === selected;
  const feedback = g?.answer_feedback.filter(match) || [];
  const displayTab = (value: string) => {
    setDetails(true);
    setTab(value);
  };
  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">{modes[session.mode].title}</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Kết quả Speaking
          </h1>
          <p className="mt-2 text-xs text-stone-500">
            {new Date(session.started_at).toLocaleString("vi-VN")} ·{" "}
            {session.answers.filter((a) => a.has_audio).length} bản ghi
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href={`/speaking?mode=${session.mode}`}>
            <RotateCcw />
            {session.mode === "FULL_TEST" ? "Thi thử lần nữa" : "Câu khác"}
          </Link>
        </Button>
      </div>
      {busy && (
        <div
          role="status"
          className="flex items-center gap-3 rounded-xl border border-teal-100 bg-teal-50 p-5 text-sm text-teal-900"
        >
          <LoaderCircle className="size-5 shrink-0 animate-spin" />
          <div>
            <p className="font-semibold">{busy}</p>
            <p className="mt-1 text-xs text-teal-700">
              Bản ghi đã lưu. Xử lý cả bài có thể mất vài phút.
            </p>
          </div>
        </div>
      )}
      {error && (
        <div>
          <ErrorNotice message={error} />
          <Button disabled={!!busy} onClick={() => process(session, !!g)}>
            <RotateCcw />
            Thử xử lý lại
          </Button>
          <p className="mt-2 text-xs text-stone-500">
            Bản ghi và phần xử lý đã hoàn thành được giữ lại.
          </p>
        </div>
      )}
      {!g && !busy && !error && (
        <EmptyState
          title="Chưa có phản hồi AI"
          description={
            session.answers.some((a) => a.has_audio)
              ? "Bản ghi của bạn đã được lưu. Bắt đầu xử lý để nhận phản hồi."
              : "Các câu hỏi trong phiên này đã được bỏ qua, chưa có audio để chấm."
          }
        >
          {session.answers.some((a) => a.has_audio) && (
            <Button onClick={() => process(session)}>Chấm bài nói</Button>
          )}
        </EmptyState>
      )}
      {g && (
        <>
          <section className="grid gap-6 rounded-2xl bg-teal-900 p-6 text-white sm:grid-cols-[210px_1fr] sm:p-8">
            <div>
              <p className="text-xs text-teal-100">Điểm AI ước tính</p>
              <p className="mt-3 text-5xl font-bold">
                {scoreText(g.scores.overall)}
                <span className="ml-2 text-xl font-normal text-teal-200">
                  / 10
                </span>
              </p>
              <p className="mt-3 text-sm font-semibold text-teal-100">
                Mức tham khảo: {g.estimated_level}
              </p>
            </div>
            <div>
              <p className="text-sm leading-7 text-teal-50">{g.summary_vi}</p>
              <p className="mt-4 text-xs leading-6 text-teal-200">
                {session.mode === "FULL_TEST"
                  ? "Đánh giá tổng thể tất cả câu trả lời, gồm follow-up. Năm tiêu chí có trọng số 20% mỗi tiêu chí."
                  : "Kết quả cho lượt luyện này. Năm tiêu chí có trọng số 20% mỗi tiêu chí."}
              </p>
            </div>
          </section>
          {g.scores.overall == null && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-900">
              <p className="font-semibold">
                Chưa đủ bằng chứng để tính tổng điểm
              </p>
              <p className="mt-1">
                Phát âm và độ trôi chảy cần audio được phân tích với độ tin cậy
                đủ tốt. Bạn vẫn có thể xem phản hồi ngôn ngữ và nghe lại bản
                ghi.
              </p>
              {session.answers
                .filter((a) => a.has_audio && a.audio_analysis?.reason_vi)
                .slice(0, 1)
                .map((a) => (
                  <p key={a.id} className="mt-2">
                    {a.audio_analysis?.reason_vi}
                  </p>
                ))}
              <Button
                className="mt-3"
                variant="outline"
                disabled={!!busy}
                onClick={() => process(session, true)}
              >
                Thử phân tích audio lại
              </Button>
            </div>
          )}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {Object.entries(criterionLabels).map(([key, label]) => (
              <button
                key={key}
                onClick={() =>
                  displayTab(key === "structures" ? "structure" : key)
                }
                className="panel p-5 text-left hover:border-teal-400"
              >
                <p className="text-xs font-semibold text-stone-500">{label}</p>
                <p className="mt-3 text-2xl font-bold text-teal-800">
                  {scoreText(g.scores[key as Criterion])}
                  <span className="ml-1 text-xs font-normal text-stone-400">
                    / 10
                  </span>
                </p>
                {g.scores[key as Criterion] == null && (
                  <p className="mt-2 text-xs text-stone-400">
                    Chưa đủ dữ liệu audio
                  </p>
                )}
              </button>
            ))}
          </div>
          <section>
            <h2 className="mb-4 text-xl font-bold">
              3 điều bạn nên cải thiện ngay
            </h2>
            <div className="grid gap-4 md:grid-cols-3">
              {g.priority_improvements.map((item, index) => (
                <article key={index} className="panel p-6">
                  <span className="text-sm font-bold text-teal-700">
                    0{index + 1}
                  </span>
                  <h3 className="mt-3 font-semibold">{item.title_vi}</h3>
                  <p className="mt-3 text-sm leading-6 text-stone-500">
                    {item.explanation_vi}
                  </p>
                  {item.example && (
                    <p className="mt-4 rounded-lg bg-teal-50 p-3 text-sm leading-6 text-teal-900">
                      {item.example}
                    </p>
                  )}
                </article>
              ))}
            </div>
          </section>
          <Button
            variant="outline"
            onClick={() => setDetails(!details)}
            aria-expanded={details}
          >
            <ChevronDown className={details ? "rotate-180" : ""} />
            {details ? "Thu gọn phân tích" : "Xem phân tích chi tiết"}
          </Button>
        </>
      )}
      <section className="panel p-5 sm:p-7">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-lg font-bold">Bản ghi & lời bạn nói</h2>
          <label className="text-xs font-medium">
            Chọn câu trả lời
            <select
              className="field mt-2 max-w-sm"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              <option value="all">Tất cả câu trả lời</option>
              {session.answers.map((a) => (
                <option key={a.id} value={a.sequence_number}>
                  Câu {a.sequence_number + 1} · Part {a.part} ·{" "}
                  {a.question_text.slice(0, 50)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mt-5 space-y-5">
          {chosen.map((a) => (
            <div key={a.id} className="rounded-xl border border-stone-100 p-4">
              <p className="eyebrow">
                Câu {a.sequence_number + 1} · Part {a.part} ·{" "}
                {duration((a.audio_duration_ms || 0) / 1000)}
              </p>
              <h3 className="mb-4 mt-2 text-sm font-semibold leading-6">
                {a.question_text}
              </h3>
              {a.has_audio ? (
                <AudioPlayer answerId={a.id} />
              ) : (
                <p className="text-sm text-stone-500">Câu hỏi đã bỏ qua.</p>
              )}
              {a.transcript !== null && a.has_audio && (
                <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-stone-600">
                  {a.transcript ||
                    "Chưa nhận dạng được lời nói trong bản ghi này."}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>
      {g && details && (
        <Tabs value={tab} onValueChange={setTab} className="space-y-5">
          <TabsList className="flex h-auto flex-wrap justify-start gap-1">
            {[
              ["overview", "Tổng quan"],
              ["content", "Nội dung"],
              ["grammar", "Ngữ pháp"],
              ["vocabulary", "Từ vựng"],
              ["pronunciation", "Phát âm"],
              ["fluency", "Độ trôi chảy"],
              ["structure", "Mạch lạc"],
              ["sentences", "Chữa từng câu"],
              ["corrected", "Bài sửa"],
              ["b2", "Bài B2 tham khảo"],
            ].map(([key, label]) => (
              <TabsTrigger key={key} value={key}>
                {label}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value="overview">
            <div className="grid gap-5 lg:grid-cols-2">
              <section className="panel p-6">
                <h2 className="mb-5 text-lg font-bold">Điểm mạnh của bạn</h2>
                <ul className="space-y-4">
                  {g.strengths.map((strength, i) => (
                    <li key={i} className="flex gap-3 text-sm leading-6">
                      <Check className="mt-1 size-4 shrink-0 text-teal-600" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </section>
              <section className="panel p-6">
                <h2 className="mb-2 text-lg font-bold">Cách trả lời tốt hơn</h2>
                <p className="mb-5 text-xs leading-5 text-stone-500">
                  Gợi ý luyện tập, không phải khuôn trả lời bắt buộc.
                </p>
                <Improvements items={g.speaking_frame} />
              </section>
            </div>
          </TabsContent>
          <TabsContent value="content">
            <section className="panel space-y-6 p-6">
              <Improvements items={g.content_feedback} />
              {feedback.map((item) => (
                <article
                  key={item.sequence_number}
                  className="rounded-xl bg-stone-50 p-5"
                >
                  <p className="eyebrow">
                    Câu {item.sequence_number + 1} · Part {item.part}
                  </p>
                  <p className="mt-3 text-sm leading-7">{item.summary_vi}</p>
                  {item.part === 2 && (
                    <dl className="mt-4 space-y-3 text-sm leading-6">
                      <div>
                        <dt className="font-semibold">Lựa chọn rõ ràng</dt>
                        <dd>
                          {item.best_option_clearly_stated === null
                            ? "Chưa đủ dữ liệu"
                            : item.best_option_clearly_stated
                              ? "Có"
                              : "Chưa"}
                        </dd>
                      </div>
                      <div>
                        <dt className="font-semibold">Phát triển lý do</dt>
                        <dd>{item.reasons_developed_vi}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold">
                          Thảo luận phương án còn lại
                        </dt>
                        <dd>{item.other_options_discussed_vi}</dd>
                      </div>
                    </dl>
                  )}
                </article>
              ))}
            </section>
          </TabsContent>
          <TabsContent value="grammar">
            <section className="panel space-y-4 p-6">
              <h2 className="text-lg font-bold">Lỗi ngữ pháp cần chú ý</h2>
              {g.errors
                .filter((e) => e.category === "grammar" && match(e))
                .map((e) => (
                  <Correction key={e.id} {...e} />
                ))}
              {!g.errors.some((e) => e.category === "grammar" && match(e)) && (
                <NoItems />
              )}
            </section>
          </TabsContent>
          <TabsContent value="vocabulary">
            <section className="panel space-y-4 p-6">
              <h2 className="text-lg font-bold">Từ vựng tự nhiên hơn</h2>
              {g.vocabulary_suggestions.filter(match).map((v, i) => (
                <div key={i} className="rounded-xl border border-stone-200 p-5">
                  <p className="eyebrow">Câu {v.sequence_number + 1}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
                    <span className="text-stone-500">{v.original}</span>
                    <ArrowRight size={15} />
                    <strong className="text-teal-800">{v.suggestion}</strong>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-stone-500">
                    {v.reason_vi}
                  </p>
                  <p className="mt-3 text-sm leading-6">{v.example}</p>
                </div>
              ))}
              {!g.vocabulary_suggestions.filter(match).length && <NoItems />}
            </section>
          </TabsContent>
          <TabsContent value="pronunciation">
            <section className="panel space-y-4 p-6">
              <h2 className="text-lg font-bold">
                Phát âm · {scoreText(g.scores.pronunciation)} / 10
              </h2>
              <p className="text-sm leading-6 text-stone-500">
                Mục tiêu là nói rõ và dễ hiểu. Phản hồi dưới đây chỉ gồm vấn đề
                có đủ bằng chứng audio; IPA chỉ hiển thị khi độ tin cậy cao.
              </p>
              {g.pronunciation_feedback.filter(match).map((p, i) => (
                <article
                  key={i}
                  className="rounded-xl border border-stone-200 p-5"
                >
                  <p className="eyebrow">
                    Câu {p.sequence_number + 1} ·{" "}
                    {(
                      {
                        individual_sound: "Âm riêng lẻ",
                        word_stress: "Trọng âm từ",
                        sentence_stress: "Trọng âm câu",
                        final_sound: "Âm cuối",
                        intonation: "Ngữ điệu",
                        clarity: "Độ rõ",
                      } as Record<string, string>
                    )[p.issue] || p.issue}
                  </p>
                  <h3 className="mt-3 text-lg font-bold">
                    {p.word}{" "}
                    {p.ipa && (
                      <span className="font-normal text-stone-500">
                        {p.ipa}
                      </span>
                    )}
                  </h3>
                  <p className="mt-3 text-sm leading-6">{p.feedback_vi}</p>
                  <p className="mt-3 rounded-lg bg-teal-50 p-3 text-sm leading-6 text-teal-900">
                    {p.suggestion}
                  </p>
                </article>
              ))}
              {!g.pronunciation_feedback.filter(match).length && (
                <p className="text-sm text-stone-500">
                  Chưa có lỗi phát âm đủ tin cậy để hiển thị.
                </p>
              )}
            </section>
          </TabsContent>
          <TabsContent value="fluency">
            <section className="panel space-y-6 p-6">
              <h2 className="text-lg font-bold">Nhịp nói của bạn</h2>
              {chosen
                .filter((a) => a.has_audio)
                .map((a) => (
                  <div key={a.id}>
                    <p className="eyebrow mb-3">Câu {a.sequence_number + 1}</p>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                      {[
                        [
                          "Thời gian",
                          duration((a.audio_duration_ms || 0) / 1000),
                        ],
                        ["Số từ", a.word_count],
                        ["Từ / phút", a.metrics.words_per_minute],
                        ["Khoảng lặng (ước lượng)", a.metrics.pause_count],
                        ["Khoảng lặng dài", a.metrics.long_pause_count],
                        ["Uh / um / erm", a.metrics.filler_count],
                        [
                          "Từ có thể là filler",
                          a.metrics.filler_candidate_count,
                        ],
                        ["Lặp từ liên tiếp", a.metrics.repetition_count],
                      ].map(([label, value]) => (
                        <div
                          key={String(label)}
                          className="rounded-xl bg-stone-50 p-4"
                        >
                          <p className="text-xs text-stone-500">{label}</p>
                          <p className="mt-2 text-lg font-semibold">
                            {value ?? "—"}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              <p className="text-xs leading-6 text-stone-500">
                Khoảng lặng được ước lượng từ năng lượng audio; có thể là khoảng
                nghỉ tự nhiên. Filler và lặp từ dựa trên transcript nên có thể
                thiếu do nhận dạng. “Well”, “like”, “actually” có thể dùng đúng
                ngữ cảnh. Tốc độ nói không được quy đổi cứng thành mức B2.
              </p>
              <Improvements items={g.fluency_feedback} />
            </section>
          </TabsContent>
          <TabsContent value="structure">
            <section className="panel p-6">
              <h2 className="mb-5 text-lg font-bold">Tổ chức ý & liên kết</h2>
              <Improvements items={g.structure_feedback} />
            </section>
          </TabsContent>
          <TabsContent value="sentences">
            <section className="panel space-y-4 p-6">
              <h2 className="text-lg font-bold">Chữa từng câu nói</h2>
              {g.sentence_corrections.filter(match).map((item, i) => (
                <Correction key={i} {...item} />
              ))}
              {!g.sentence_corrections.filter(match).length && <NoItems />}
            </section>
          </TabsContent>
          {[
            ["corrected", "Bản sửa giữ ý của bạn", "corrected_transcript"],
            ["b2", "Bài nói B2 tham khảo", "improved_b2_answer"],
          ].map(([value, title, field]) => (
            <TabsContent key={value} value={value}>
              <section className="panel space-y-5 p-6">
                <h2 className="text-lg font-bold">{title}</h2>
                <p className="text-sm text-stone-500">
                  {value === "b2"
                    ? "Học cách diễn đạt tự nhiên, dễ nói từ chính ý tưởng của bạn."
                    : "Sửa ngữ pháp, từ vựng và liên kết nhẹ, giữ nội dung câu trả lời gốc."}
                </p>
                {feedback.map((item) => (
                  <article
                    key={item.sequence_number}
                    className="rounded-xl bg-teal-50/50 p-5"
                  >
                    <p className="eyebrow">
                      Câu {item.sequence_number + 1} · Part {item.part}
                    </p>
                    <p className="mt-3 whitespace-pre-wrap text-base leading-8">
                      {item[
                        field as "corrected_transcript" | "improved_b2_answer"
                      ] || "Chưa có lời nói để tạo bản tham khảo."}
                    </p>
                  </article>
                ))}
              </section>
            </TabsContent>
          ))}
        </Tabs>
      )}
      <p className="border-t border-stone-200 pt-5 text-xs leading-6 text-stone-500">
        {disclaimer}
      </p>
    </div>
  );
}
function Improvements({ items }: { items: Improvement[] }) {
  return (
    <div className="space-y-5">
      {items.map((item, i) => (
        <div key={i}>
          <h3 className="text-sm font-semibold">{item.title_vi}</h3>
          <p className="mt-2 text-sm leading-7 text-stone-500">
            {item.explanation_vi}
          </p>
          {item.example && (
            <p className="mt-2 rounded-lg bg-stone-50 p-3 text-sm leading-6">
              {item.example}
            </p>
          )}
        </div>
      ))}
      {!items.length && <NoItems />}
    </div>
  );
}
function Correction({
  sequence_number,
  original,
  corrected,
  explanation_vi,
}: {
  sequence_number: number;
  original: string;
  corrected: string;
  explanation_vi: string;
}) {
  return (
    <div className="rounded-xl border border-stone-200 p-5">
      <p className="eyebrow mb-3">Câu trả lời {sequence_number + 1}</p>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-semibold text-stone-400">
            CÂU BẠN NÓI
          </p>
          <p className="text-sm leading-7 text-stone-600">{original}</p>
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold text-teal-700">SỬA THÀNH</p>
          <p className="text-sm font-medium leading-7 text-teal-900">
            {corrected}
          </p>
        </div>
      </div>
      <p className="mt-4 border-t border-stone-100 pt-3 text-sm leading-7 text-stone-500">
        {explanation_vi}
      </p>
    </div>
  );
}
function NoItems() {
  return (
    <p className="text-sm leading-6 text-stone-500">
      Chưa có mục cần sửa được xác định trong phần này.
    </p>
  );
}
