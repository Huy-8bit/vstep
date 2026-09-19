"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpenText, Check, Clock3, Flag } from "lucide-react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api } from "@/services/api";
import { ReadingPlacement } from "./reading-placement";
import { ReadingPassage } from "./reading-passage";
import { useReadingAutosave } from "./use-reading-autosave";
import { duration, options, questionTypes, type ReadingSession } from "./types";
export function ReadingExam({ id }: { id: string }) {
  return (
    <RequireAuth>
      <LoadExam id={id} />
    </RequireAuth>
  );
}
function LoadExam({ id }: { id: string }) {
  const [data, setData] = useState<ReadingSession | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();
  const load = useCallback(async () => {
    setError("");
    try {
      const s = await api<ReadingSession>(`/reading/sessions/${id}`);
      if (s.status !== "IN_PROGRESS") router.replace(`/reading/result/${id}`);
      else setData(s);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [id, router]);
  useEffect(() => {
    void load();
  }, [load]);
  return data ? (
    <Workspace session={data} />
  ) : (
    <div className="mx-auto max-w-4xl p-8">
      {error ? (
        <>
          <ErrorNotice message={error} />
          <Button onClick={load}>Thử lại</Button>
        </>
      ) : (
        <Loading text="Đang mở bài Reading..." />
      )}
    </div>
  );
}
function Workspace({ session }: { session: ReadingSession }) {
  const router = useRouter();
  const { user } = useAuth();
  const [index, setIndex] = useState(0);
  const [mobile, setMobile] = useState("passage");
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState("");
  const [clockOffset] = useState(
    () => Date.parse(session.server_now) - Date.now(),
  );
  const [now, setNow] = useState(() => Date.now() + clockOffset);
  const submitLock = useRef(false);
  const expiredRetry = useRef(0);
  const questionsRoot = useRef<HTMLDivElement>(null);
  const closed = useCallback(
    () => router.replace(`/reading/result/${session.id}`),
    [router, session.id],
  );
  const save = useReadingAutosave(session, user!.id, closed);
  const questions = session.question_ids.map((id) =>
    session.passages.flatMap((p) => p.questions).find((q) => q.id === id)!,
  );
  const question = questions[index];
  const passage = session.passages.find((p) => p.id === question.passage_id)!;
  const passageIndex = session.passages.indexOf(passage);
  const answer = save.values[question.id];
  const remaining = session.expires_at
    ? Math.max(0, Math.ceil((Date.parse(session.expires_at) - now) / 1000))
    : null;
  const expired = remaining === 0;
  const answered = Object.values(save.values).filter(
    (a) => a.selected_answer,
  ).length;
  const marked = Object.values(save.values).filter(
    (a) => a.is_marked_for_review,
  ).length;
  const submitRef = useRef<(expired: boolean) => Promise<void>>(async () => {});
  async function submit(atDeadline = false) {
    if (submitLock.current) return;
    submitLock.current = true;
    setBusy(true);
    setError("");
    try {
      await save.submit(atDeadline);
      closed();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
      submitLock.current = false;
    }
  }
  useEffect(() => {
    submitRef.current = submit;
  });
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now() + clockOffset), 250);
    return () => clearInterval(timer);
  }, [clockOffset]);
  useEffect(() => {
    if (expired && Date.now() - expiredRetry.current > 5000) {
      expiredRetry.current = Date.now();
      void submitRef.current(true);
    }
  }, [expired, now]);
  const tickRef = useRef(save.tick);
  useEffect(() => {
    tickRef.current = save.tick;
  });
  useEffect(() => {
    const timer = setInterval(() => {
      if (!document.hidden && document.hasFocus() && !busy && !expired)
        tickRef.current(question.id);
    }, 1000);
    return () => clearInterval(timer);
  }, [question.id, busy, expired]);
  useEffect(() => {
    questionsRoot.current?.scrollTo({ top: 0 });
  }, [index]);
  const changeRef = useRef(save.change);
  useEffect(() => {
    changeRef.current = save.change;
  });
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if (
        event.ctrlKey ||
        event.metaKey ||
        event.altKey ||
        busy ||
        expired ||
        confirm ||
        /INPUT|SELECT|TEXTAREA/.test(
          (event.target as HTMLElement)?.tagName || "",
        )
      )
        return;
      const letter = event.key.toUpperCase();
      if (options.includes(letter as (typeof options)[number])) {
        event.preventDefault();
        changeRef.current(question.id, {
          selected_answer: letter as (typeof options)[number],
        });
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, [question.id, busy, expired, confirm]);
  function go(number: number) {
    setIndex(number);
    setMobile("questions");
  }
  async function leave() {
    setBusy(true);
    await save.flush();
    if (save.hasPending()) {
      setError(
        "Đáp án chưa đồng bộ hết. Bản dự phòng vẫn được giữ trên thiết bị; thử lưu lại khi có mạng.",
      );
      setBusy(false);
      return;
    }
    router.push("/reading/history");
  }
  return (
    <div className="flex h-dvh min-h-[480px] flex-col overflow-hidden bg-[#f6f7f4]">
      <header className="shrink-0 border-b border-stone-200 bg-white px-4 py-3 sm:px-7">
        <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3">
          <h1 className="flex items-center gap-2 text-lg font-bold">
            <BookOpenText className="size-5 text-teal-800" />
            VSTEP Reading
          </h1>
          <div className="flex items-center gap-4">
            <span
              className={`flex items-center gap-2 text-sm font-semibold tabular-nums ${remaining !== null && remaining < 300 ? "text-red-700" : "text-teal-900"}`}
            >
              <Clock3 size={16} />
              {remaining === null
                ? duration((now - Date.parse(session.started_at)) / 1000)
                : duration(remaining)}
            </span>
            <Button
              size="sm"
              disabled={busy || expired}
              onClick={() => setConfirm(true)}
            >
              Nộp bài
            </Button>
          </div>
        </div>
      </header>
      <div className="flex shrink-0 items-center justify-between gap-3 overflow-x-auto border-b border-stone-200 bg-white px-4 py-2 sm:px-7">
        <div className="flex gap-2">
          {session.passages.map((p, i) => (
            <button
              key={p.id}
              onClick={() => {
                setIndex(questions.findIndex((q) => q.passage_id === p.id));
                setMobile("passage");
              }}
              className={`whitespace-nowrap rounded-lg px-4 py-2 text-xs font-semibold ${p.id === passage.id ? "bg-teal-800 text-white" : "bg-stone-50 text-stone-500"}`}
            >
              Passage {i + 1}
            </button>
          ))}
        </div>
        <span
          className="hidden whitespace-nowrap text-xs text-stone-500 sm:block"
          role="status"
        >
          {save.status}
        </span>
      </div>
      <div className="flex shrink-0 gap-2 px-4 py-2 lg:hidden">
        {[
          ["passage", "Bài đọc"],
          ["questions", `Câu hỏi ${index + 1}`],
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setMobile(key)}
            aria-pressed={mobile === key}
            className={`flex-1 rounded-lg py-2 text-xs font-semibold ${mobile === key ? "bg-teal-100 text-teal-900" : "bg-white text-stone-500"}`}
          >
            {label}
          </button>
        ))}
      </div>
      {(expired || error || save.error || save.warning) && (
        <div
          className="max-h-28 shrink-0 overflow-y-auto border-b border-amber-100 bg-amber-50 px-5 py-2 text-xs leading-5 text-amber-900"
          role="status"
        >
          {expired
            ? "Đã hết giờ. Đang nộp các đáp án đã lưu; hệ thống sẽ thử lại khi kết nối trở lại."
            : error || save.error || save.warning}
        </div>
      )}
      {Object.keys(save.conflicts).length > 0 && (
        <div className="max-h-40 shrink-0 overflow-y-auto bg-amber-50 px-5 py-3 text-xs">
          <p className="font-semibold">Có đáp án khác nhau giữa các tab:</p>
          {Object.entries(save.conflicts).map(([id, server]) => (
            <div key={id} className="mt-2 flex flex-wrap items-center gap-3">
              <span>
                Câu {session.question_ids.indexOf(id) + 1}: thiết bị{" "}
                {save.values[id].selected_answer || "trống"}, máy chủ{" "}
                {server.selected_answer || "trống"}
              </span>
              <Button
                size="sm"
                variant="outline"
                disabled={busy || expired}
                onClick={() => save.resolve(id, true)}
              >
                Giữ trên thiết bị
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={busy || expired}
                onClick={() => save.resolve(id, false)}
              >
                Dùng bản máy chủ
              </Button>
            </div>
          ))}
        </div>
      )}
      <main className="mx-auto grid min-h-0 w-full max-w-[1600px] flex-1 lg:grid-cols-[1.15fr_1fr]">
        <section
          className={`min-h-0 bg-white lg:block ${mobile === "passage" ? "block" : "hidden"}`}
        >
          <ReadingPassage passage={passage} />
        </section>
        <section
          ref={questionsRoot}
          className={`min-h-0 overflow-y-auto overscroll-contain border-stone-200 bg-[#f8f9f6] p-5 sm:p-8 lg:block lg:border-l ${mobile === "questions" ? "block" : "hidden"}`}
          aria-label="Câu hỏi"
        >
          <div className="mb-5 flex items-center justify-between gap-3">
            <p className="eyebrow">
              Passage {passageIndex + 1} ·{" "}
              {questionTypes[question.question_type] || "Câu hỏi từ đề riêng"}
            </p>
            <button
              disabled={busy || expired}
              aria-pressed={answer.is_marked_for_review}
              title="Đánh dấu xem lại"
              onClick={() =>
                save.change(question.id, {
                  is_marked_for_review: !answer.is_marked_for_review,
                })
              }
              className={`flex items-center gap-1.5 rounded-lg p-2 text-xs ${answer.is_marked_for_review ? "bg-amber-100 text-amber-900" : "text-stone-500"}`}
            >
              <Flag size={15} />
              {answer.is_marked_for_review ? "Đã đánh dấu" : "Xem lại"}
            </button>
          </div>
          <fieldset disabled={busy || expired}>
            <legend className="mb-6 whitespace-pre-wrap text-lg font-semibold leading-8">
              <span className="mr-2 text-teal-800">{index + 1}.</span>
              {question.question_text}
            </legend>
            {question.source_question_number &&
              question.source_question_number !== index + 1 && (
                <p className="mb-4 text-xs text-stone-500">
                  Số câu trong nguồn: {question.source_question_number}
                </p>
              )}
            <ReadingPlacement question={question} passage={passage} />
            <div className="space-y-3">
              {options.map((letter) => (
                <label
                  key={letter}
                  className={`flex cursor-pointer items-start gap-3 rounded-xl border p-4 text-sm leading-7 transition ${answer.selected_answer === letter ? "border-teal-600 bg-teal-50 ring-1 ring-teal-600" : "border-stone-200 bg-white hover:border-teal-300"}`}
                >
                  <input
                    className="mt-2 size-4 shrink-0 accent-teal-800"
                    type="radio"
                    name={question.id}
                    value={letter}
                    checked={answer.selected_answer === letter}
                    onChange={() =>
                      save.change(question.id, { selected_answer: letter })
                    }
                  />
                  <span className="font-bold">{letter}.</span>
                  <span>{question.options[letter]}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="mt-5 flex items-center justify-between gap-3">
            <Button
              variant="ghost"
              size="sm"
              disabled={!answer.selected_answer || busy || expired}
              onClick={() =>
                save.change(question.id, { selected_answer: null })
              }
            >
              Xóa lựa chọn
            </Button>
            <p className="hidden text-xs text-stone-400 sm:block">
              Phím tắt A / B / C / D
            </p>
          </div>
          <div className="mt-6 flex justify-between gap-3">
            <Button
              variant="outline"
              disabled={index === 0}
              onClick={() => go(index - 1)}
            >
              ← Câu trước
            </Button>
            <Button
              variant="outline"
              disabled={index === questions.length - 1}
              onClick={() => go(index + 1)}
            >
              Câu tiếp →
            </Button>
          </div>
        </section>
      </main>
      <footer className="shrink-0 border-t border-stone-200 bg-white px-4 py-3 sm:px-7">
        <div className="mx-auto max-w-[1500px]">
          <div className="mb-2 flex flex-wrap justify-between gap-2 text-[11px] text-stone-500">
            <p>
              <span className="font-semibold text-teal-800">
                {answered}/{questions.length} đã trả lời
              </span>{" "}
              · {questions.length - answered} chưa làm · {marked} xem lại
            </p>
            <button
              disabled={busy}
              onClick={leave}
              className="font-semibold text-teal-800"
            >
              Lưu và thoát
            </button>
          </div>
          <nav
            aria-label="Chuyển câu hỏi"
            className="grid grid-cols-10 gap-1.5 sm:grid-cols-20"
          >
            {questions.map((q, i) => {
              const a = save.values[q.id];
              return (
                <button
                  key={q.id}
                  aria-label={`Câu ${i + 1}, ${a.selected_answer ? "đã trả lời" : "chưa trả lời"}${a.is_marked_for_review ? ", đánh dấu xem lại" : ""}`}
                  aria-current={i === index ? "step" : undefined}
                  onClick={() => go(i)}
                  className={`relative flex h-8 items-center justify-center rounded-md border text-xs font-semibold ${i === index ? "ring-2 ring-teal-800 ring-offset-1" : ""} ${a.selected_answer ? "border-teal-200 bg-teal-100 text-teal-900" : "border-stone-200 text-stone-500"} ${a.is_marked_for_review ? "border-amber-400 bg-amber-50" : ""}`}
                >
                  {i + 1}
                  {a.is_marked_for_review && (
                    <span className="absolute right-0 top-0 text-[9px] text-amber-700">
                      ★
                    </span>
                  )}
                  {a.selected_answer && (
                    <Check className="absolute bottom-0 right-0 size-2 text-teal-700" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </footer>
      <Dialog
        open={confirm}
        onOpenChange={(open) => {
          if (!busy) setConfirm(open);
        }}
      >
        <DialogContent>
          <DialogTitle className="text-xl font-bold">
            Nộp bài Reading
          </DialogTitle>
          <dl className="my-6 space-y-3 text-sm">
            <div className="flex justify-between">
              <dt>Đã trả lời</dt>
              <dd>
                {answered}/{questions.length}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt>Chưa trả lời</dt>
              <dd>{questions.length - answered}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Đánh dấu xem lại</dt>
              <dd>{marked}</dd>
            </div>
          </dl>
          <DialogDescription className="mb-5 text-xs leading-6 text-stone-500">
            Bài được khóa sau khi nộp. Các câu bỏ trống không được tính điểm.
          </DialogDescription>
          {error && <ErrorNotice message={error} />}
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => setConfirm(false)}
            >
              Tiếp tục làm
            </Button>
            <Button disabled={busy} onClick={() => submit(false)}>
              {busy ? "Đang nộp..." : "Nộp và xem kết quả"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
