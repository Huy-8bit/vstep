"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCheck,
  Clock3,
  CloudOff,
  LoaderCircle,
  Send,
} from "lucide-react";
import { Brand } from "@/components/shell";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { ErrorNotice, Loading } from "@/components/feedback";
import { AiProgressOverlay } from "@/components/ui/ai-progress";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { QuestionCard } from "@/features/writing/practice-setup";
import { useAutosave } from "@/hooks/use-autosave";
import { api, post } from "@/services/api";
import { cn, countWords } from "@/lib/utils";
import type { Exam } from "@/types";

function Workspace({ initial }: { initial: Exam }) {
  const router = useRouter();
  const { user } = useAuth();
  const [task, setTask] = useState(0);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [now, setNow] = useState(() => Date.now());
  const [offset, setOffset] = useState(
    () => new Date(initial.server_now).getTime() - Date.now(),
  );
  const draft = useAutosave(initial, user!.id);
  const autoSubmitted = useRef(false);
  const submitting = useRef(false);
  const attempt = initial.attempts[task];
  const answer = draft.answers[attempt.id] || "";
  const words = countWords(answer);
  const expires = initial.expires_at
    ? new Date(initial.expires_at).getTime()
    : null;
  const seconds = expires
    ? Math.max(0, Math.ceil((expires - (now + offset)) / 1000))
    : null;
  const expired = seconds === 0;

  async function submit() {
    if (submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    setConfirm(false);
    try {
      const answers = await draft.prepareSubmit();
      const exam = await post<Exam>(`/exams/${initial.id}/submit`, { answers });
      draft.complete(exam);
      router.replace(`/result?id=${exam.attempts[0].id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
      submitting.current = false;
    }
  }
  const submitRef = useRef(submit);
  useEffect(() => {
    submitRef.current = submit;
  });
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);
  useEffect(() => {
    const sync = async () => {
      try {
        const exam = await api<Exam>(`/exams/${initial.id}`);
        setOffset(new Date(exam.server_now).getTime() - Date.now());
        if (exam.status !== "IN_PROGRESS" && !submitting.current) {
          autoSubmitted.current = true;
          await submitRef.current();
        }
      } catch {
        /* Autosave reports connectivity; retry clock sync on next interval. */
      }
    };
    const interval = setInterval(sync, 30000);
    window.addEventListener("online", sync);
    return () => {
      clearInterval(interval);
      window.removeEventListener("online", sync);
    };
  }, [initial.id]);
  useEffect(() => {
    if (expired && !autoSubmitted.current) {
      autoSubmitted.current = true;
      void submitRef.current();
    }
  }, [expired]);
  const time =
    seconds == null
      ? "Không giới hạn"
      : `${Math.floor(seconds / 60)
          .toString()
          .padStart(2, "0")}:${(seconds % 60).toString().padStart(2, "0")}`;

  return (
    <div className="min-h-screen">
      <header className="border-b border-stone-200 bg-white px-5 py-4 sm:px-8">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-4">
          <Brand />
          <nav
            className="order-3 flex w-full gap-2 sm:order-none sm:w-auto"
            aria-label="Chọn bài viết"
          >
            {initial.attempts.map((a, i) => (
              <Button
                key={a.id}
                variant={task === i ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setTask(i)}
              >
                Task {a.task_type}
                <span className="text-[10px] opacity-60">
                  {countWords(draft.answers[a.id])} từ
                </span>
              </Button>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold tabular-nums",
                seconds !== null && seconds < 300
                  ? "bg-red-50 text-red-700"
                  : "bg-stone-50 text-stone-600",
              )}
              aria-label={`Thời gian còn lại ${time}`}
            >
              <Clock3 size={16} />
              {time}
            </div>
            <Button
              size="sm"
              disabled={busy}
              onClick={() => (expired ? submit() : setConfirm(true))}
            >
              {busy ? <LoaderCircle className="animate-spin" /> : <Send />}Nộp
              bài
            </Button>
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-[1500px] px-5 py-5 sm:px-8">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-2 text-xs text-stone-500">
          <p>
            {initial.mode === "FULL_TEST"
              ? "Thi thử Writing · 60 phút cho cả hai Task"
              : `Luyện Task ${attempt.task_type} · ${initial.expires_at ? "Thời gian luyện tập đề xuất" : "Viết theo nhịp của bạn"}`}
          </p>
          <span
            aria-live="polite"
            className={cn(
              "flex items-center gap-1.5",
              draft.error ? "text-amber-700" : "text-teal-700",
            )}
          >
            {draft.error ? (
              <CloudOff size={14} />
            ) : draft.status === "Đã lưu" ? (
              <CheckCheck size={14} />
            ) : (
              <LoaderCircle size={14} className="animate-spin" />
            )}
            {draft.status}
          </span>
        </div>
        {error && <ErrorNotice message={error} />}
        {draft.error && <ErrorNotice message={draft.error} />}
        {draft.localWarning && <ErrorNotice message={draft.localWarning} />}
        {draft.restored && (
          <p className="mb-4 rounded-lg bg-teal-50 px-4 py-3 text-xs text-teal-800">
            Đã khôi phục bản nháp trên thiết bị này.
          </p>
        )}
        {expired && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            Đã hết giờ. Máy chủ giữ bản bài làm được lưu trước thời hạn. Nếu mất
            kết nối, bản nháp trên thiết bị vẫn được giữ để bạn xem lại.
            {error && (
              <Button
                className="ml-3"
                size="sm"
                onClick={submit}
                disabled={busy}
              >
                Thử nộp lại
              </Button>
            )}
          </div>
        )}
        <div className="grid items-stretch gap-5 lg:grid-cols-[.9fr_1.1fr]">
          <section className="panel p-6 sm:p-8">
            <div className="mb-7 flex items-center justify-between">
              <h1 className="text-base font-bold">Đề bài</h1>
              <span className="text-xs text-stone-400">
                {attempt.task_type === 1 ? "Thư / Email" : "Bài luận"}
              </span>
            </div>
            <QuestionCard question={attempt.question} />
            <div className="mt-9 border-t border-stone-100 pt-5 text-xs leading-6 text-stone-400">
              Đọc kỹ yêu cầu và viết câu trả lời bằng tiếng Anh. Hệ thống chỉ
              cung cấp phản hồi sau khi bạn nộp bài.
            </div>
          </section>
          <section className="panel flex min-h-[560px] flex-col overflow-hidden">
            <div className="flex items-center justify-between border-b border-stone-100 px-6 py-5">
              <label htmlFor="answer" className="font-bold">
                Bài viết của bạn
              </label>
              <span
                className={cn(
                  "text-xs font-medium",
                  words < attempt.question.minimum_words
                    ? "text-amber-700"
                    : "text-teal-700",
                )}
              >
                {words} / {attempt.question.minimum_words} từ tối thiểu
              </span>
            </div>
            {draft.conflicts[attempt.id] && (
              <div className="m-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <p className="mb-3 text-sm text-amber-900">
                  Có bản mới hơn trên máy chủ. Chọn bản bạn muốn giữ.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={() =>
                      draft
                        .resolve(attempt.id, true)
                        .catch((e) => setError(e.message))
                    }
                  >
                    Giữ bản trên thiết bị
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      draft
                        .resolve(attempt.id, false)
                        .catch((e) => setError(e.message))
                    }
                  >
                    Dùng bản trên máy chủ
                  </Button>
                </div>
              </div>
            )}
            <textarea
              key={attempt.id}
              id="answer"
              lang="en"
              spellCheck={false}
              autoCorrect="off"
              autoCapitalize="off"
              aria-describedby="word-guidance"
              className="exam-editor min-h-96 w-full flex-1 resize-y bg-transparent p-6 outline-none placeholder:text-stone-300 disabled:bg-stone-50 sm:p-8"
              placeholder={
                attempt.task_type === 1
                  ? "Bắt đầu viết thư bằng tiếng Anh tại đây..."
                  : "Bắt đầu viết bài luận bằng tiếng Anh tại đây..."
              }
              value={answer}
              maxLength={20000}
              disabled={busy || expired}
              onChange={(event) => draft.change(attempt.id, event.target.value)}
            />
            <div
              id="word-guidance"
              className="flex items-center justify-between gap-3 border-t border-stone-100 bg-stone-50/50 px-6 py-4 text-xs"
            >
              <span
                className={
                  words < attempt.question.minimum_words
                    ? "text-amber-700"
                    : "text-teal-700"
                }
              >
                {words < attempt.question.minimum_words
                  ? `Cần thêm ${attempt.question.minimum_words - words} từ để đạt độ dài tối thiểu.`
                  : "Đã đạt số từ tối thiểu."}
              </span>
              <span className="hidden text-stone-400 sm:inline">
                Tự động lưu
              </span>
            </div>
          </section>
        </div>
        <div className="mt-5 flex justify-between">
          <Button asChild variant="ghost" size="sm">
            <Link href="/history">Lưu và quay lại sau</Link>
          </Button>
          {initial.attempts.length > 1 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setTask(task === 0 ? 1 : 0)}
            >
              Chuyển sang Task {task === 0 ? 2 : 1}
              <ArrowRight />
            </Button>
          )}
        </div>
      </div>
      <Dialog open={confirm} onOpenChange={setConfirm}>
        <DialogContent>
          <DialogTitle className="text-xl font-bold">
            Nộp{" "}
            {initial.mode === "FULL_TEST" ? "cả hai bài Writing" : "bài viết"}?
          </DialogTitle>
          <DialogDescription className="mb-5 mt-3 text-sm leading-6 text-stone-500">
            Sau khi nộp, bài viết sẽ được khóa và gửi đến OpenAI để chấm, phân
            tích lỗi và đề xuất cải thiện.
          </DialogDescription>
          <div className="mb-6 space-y-3">
            {initial.attempts.map((a) => (
              <div
                key={a.id}
                className="flex justify-between rounded-lg bg-stone-50 p-3 text-sm"
              >
                <span>Task {a.task_type}</span>
                <span
                  className={
                    countWords(draft.answers[a.id]) < a.question.minimum_words
                      ? "text-amber-700"
                      : "text-teal-700"
                  }
                >
                  {countWords(draft.answers[a.id])} từ{" "}
                  {countWords(draft.answers[a.id]) < a.question.minimum_words &&
                    "· Chưa đủ từ"}
                </span>
              </div>
            ))}
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" onClick={() => setConfirm(false)}>
              Viết tiếp
            </Button>
            <Button onClick={submit}>
              Nộp và nhận phản hồi
              <Send />
            </Button>
          </div>
        </DialogContent>
      </Dialog>
      {busy && (
        <AiProgressOverlay
          title={
            initial.mode === "FULL_TEST"
              ? "AI đang chấm cả hai bài Writing"
              : "AI đang chấm bài viết của bạn"
          }
        />
      )}
    </div>
  );
}

function LoadExam({ id }: { id: string }) {
  const [exam, setExam] = useState<Exam | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();
  const load = useCallback(() => {
    api<Exam>(`/exams/${id}`)
      .then((e) => {
        setError("");
        if (e.status !== "IN_PROGRESS")
          router.replace(`/result?id=${e.attempts[0].id}`);
        else setExam(e);
      })
      .catch((e) => setError(e.message));
  }, [id, router]);
  useEffect(() => {
    load();
  }, [load]);
  if (error)
    return (
      <div className="mx-auto max-w-xl p-8">
        <ErrorNotice message={error} />
        <Button onClick={load}>Thử tải lại</Button>
        <Button asChild variant="ghost">
          <Link href="/history">Về lịch sử</Link>
        </Button>
      </div>
    );
  return exam ? (
    <Workspace initial={exam} />
  ) : (
    <Loading text="Đang mở bài viết..." />
  );
}
export function ExamWorkspace({ id }: { id: string }) {
  return (
    <RequireAuth>
      <LoadExam id={id} />
    </RequireAuth>
  );
}
