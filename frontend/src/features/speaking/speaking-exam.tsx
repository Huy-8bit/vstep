"use client";
import { IdeaMap } from "./idea-map";
import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AudioLines,
  Check,
  Clock3,
  Mic,
  MicOff,
  Square,
  Volume2,
} from "lucide-react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api, audioBlob, post } from "@/services/api";
import { useRecorder } from "./use-recorder";
import { AudioPlayer } from "./audio-player";
import {
  duration,
  modes,
  topics,
  type SpeakingAnswer,
  type SpeakingSession,
} from "./types";

export function SpeakingExam({ id }: { id: string }) {
  return (
    <RequireAuth>
      <Exam id={id} />
    </RequireAuth>
  );
}
function Exam({ id }: { id: string }) {
  const [session, setSession] = useState<SpeakingSession | null>(null);
  const [error, setError] = useState("");
  const [now, setNow] = useState(() => Date.now());
  const router = useRouter();
  const load = useCallback(async () => {
    try {
      setError("");
      const data = await api<SpeakingSession>(`/speaking/sessions/${id}`);
      if (data.status !== "IN_PROGRESS") {
        router.replace(`/speaking/result/${id}`);
        return;
      }
      setSession(data);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [id, router]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  async function complete() {
    try {
      await post(`/speaking/sessions/${id}/complete`);
      router.replace(`/speaking/result/${id}`);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (!session)
    return (
      <div className="mx-auto max-w-5xl p-8">
        {error ? (
          <>
            <ErrorNotice message={error} />
            <Button onClick={load}>Thử lại</Button>
          </>
        ) : (
          <Loading text="Đang mở phòng Speaking..." />
        )}
      </div>
    );
  const elapsed = Math.max(
    0,
    Math.floor((now - Date.parse(session.started_at)) / 1000),
  );
  return (
    <div className="min-h-screen bg-[#f6f7f4]">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4">
          <span className="flex items-center gap-2 text-lg font-bold">
            <AudioLines className="text-teal-700" />
            VSTEP Speaking
          </span>
          <div className="flex items-center gap-4 text-sm">
            <span className="rounded-full bg-teal-50 px-3 py-1 text-teal-800">
              {session.mode === "FULL_TEST" ? "Thi thử" : "Luyện tập"} · Part{" "}
              {session.current_part}
            </span>
            <span className="flex items-center gap-2 tabular-nums">
              <Clock3 size={16} />
              {duration(elapsed)}
              {session.mode === "FULL_TEST" && (
                <span className="text-stone-400">/ ~12:00</span>
              )}
            </span>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-5 py-7 sm:py-10">
        <div className="mb-7 flex items-center justify-between gap-4">
          <div>
            <p className="eyebrow">{modes[session.mode].title}</p>
            <p className="mt-2 text-xs text-stone-500">
              Câu{" "}
              {Math.min(session.current_sequence + 1, session.total_questions)}{" "}
              / {session.total_questions}
            </p>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3].map((part) => (
              <span
                key={part}
                className={`rounded-full px-3 py-2 text-xs font-semibold ${session.current_part === part ? "bg-teal-800 text-white" : "bg-stone-100 text-stone-400"}`}
              >
                Part {part}
              </span>
            ))}
          </div>
        </div>
        <div className="mb-8 h-1 overflow-hidden rounded bg-stone-200">
          <div
            className="h-full bg-teal-700 transition-all"
            style={{
              width: `${(session.current_sequence / session.total_questions) * 100}%`,
            }}
          />
        </div>
        {error && <ErrorNotice message={error} />}
        {session.current_question ? (
          <RecordingQuestion
            key={session.current_sequence}
            session={session}
            onNext={setSession}
            onComplete={complete}
          />
        ) : (
          <section className="panel p-10 text-center">
            <Check className="mx-auto mb-4 size-10 text-teal-700" />
            <h1 className="text-2xl font-bold">
              Bạn đã trả lời hết các câu hỏi.
            </h1>
            <p className="my-5 text-sm text-stone-500">
              Nộp phiên để mở bản ghi và nhận phản hồi Speaking.
            </p>
            <Button onClick={complete}>Hoàn thành bài nói</Button>
          </section>
        )}
      </main>
    </div>
  );
}
function RecordingQuestion({
  session,
  onNext,
  onComplete,
}: {
  session: SpeakingSession;
  onNext: (s: SpeakingSession) => void;
  onComplete: () => Promise<void>;
}) {
  const { user } = useAuth();
  const router = useRouter();
  const question = session.current_question!;
  const full = session.mode === "FULL_TEST";
  const [answer, setAnswer] = useState<SpeakingAnswer | null>(
    session.answers.find(
      (a) => a.sequence_number === question.sequence_number,
    ) || null,
  );
  const recorder = useRecorder(
    `${user!.id}:${session.id}:${question.sequence_number}`,
    session.limits.max_audio_seconds,
    session.limits.max_audio_mb,
  );
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [ttsNotice, setTtsNotice] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const tts = useRef<HTMLAudioElement | null>(null);
  const ttsUrl = useRef("");
  const ttsEpoch = useRef(0);
  const actionLock = useRef(false);
  const recording = recorder.state === "recording";
  const pending = !!recorder.blob;
  const hasAudio = !!answer?.has_audio;
  const clearTts = useCallback(() => {
    ttsEpoch.current++;
    tts.current?.pause();
    if (ttsUrl.current) URL.revokeObjectURL(ttsUrl.current);
    ttsUrl.current = "";
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);
  useEffect(
    () => () => {
      ttsEpoch.current++;
      tts.current?.pause();
      if (ttsUrl.current) URL.revokeObjectURL(ttsUrl.current);
      window.speechSynthesis?.cancel();
    },
    [],
  );
  useEffect(() => {
    const leave = (e: BeforeUnloadEvent) => {
      if (recording || pending) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", leave);
    return () => window.removeEventListener("beforeunload", leave);
  }, [recording, pending]);
  async function exclusive(label: string, action: () => Promise<void>) {
    if (actionLock.current) return;
    actionLock.current = true;
    setBusy(label);
    setError("");
    try {
      await action();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      actionLock.current = false;
      setBusy("");
    }
  }
  async function ensureAnswer() {
    if (answer) return answer;
    const created = await post<SpeakingAnswer>(
      `/speaking/sessions/${session.id}/answers`,
      { sequence_number: question.sequence_number },
    );
    setAnswer(created);
    return created;
  }
  async function upload(blob: Blob) {
    const target = await ensureAnswer();
    const data = new FormData();
    data.append(
      "file",
      blob,
      `answer.${blob.type.includes("mp4") ? "mp4" : blob.type.includes("ogg") ? "ogg" : "webm"}`,
    );
    const saved = await api<SpeakingAnswer>(
      `/speaking/answers/${target.id}/audio`,
      { method: "POST", body: data },
    );
    setAnswer(saved);
    await recorder.flush();
    await recorder.discard();
    return saved;
  }
  async function start() {
    clearTts();
    await exclusive("Đang mở microphone...", async () => {
      await recorder.start(async () => {
        await ensureAnswer();
      });
    });
  }
  async function stop() {
    await exclusive(
      full ? "Đang tải bản ghi..." : "Đang lưu bản ghi...",
      async () => {
        const take = await recorder.stop();
        if (full && take) await upload(take);
      },
    );
  }
  async function next(skip = false) {
    await exclusive("Đang lưu câu trả lời...", async () => {
      if (recorder.blob && !skip) await upload(recorder.blob);
      const updated = await post<SpeakingSession>(
        `/speaking/sessions/${session.id}/next`,
        { sequence_number: question.sequence_number, skip },
      );
      if (skip) await recorder.discard();
      clearTts();
      onNext(updated);
      if (!updated.current_question) await onComplete();
    });
  }
  async function leave() {
    await exclusive("Đang lưu phiên...", async () => {
      const take = recording ? await recorder.stop() : recorder.blob;
      if (take) await upload(take);
      clearTts();
      router.push("/speaking/history");
    });
  }
  async function listen() {
    if (speaking) {
      clearTts();
      return;
    }
    setTtsNotice("");
    setSpeaking(true);
    const epoch = ++ttsEpoch.current;
    const text = [
      question.situation,
      question.question_text,
      ...question.options,
      ...question.suggested_ideas,
    ]
      .filter(Boolean)
      .join(". ");
    const fallback = () => {
      if (epoch !== ttsEpoch.current) return;
      if (!("speechSynthesis" in window)) {
        setTtsNotice(
          "Trình duyệt chưa hỗ trợ đọc câu hỏi. Bạn có thể đọc đề trên màn hình.",
        );
        setSpeaking(false);
        return;
      }
      const speech = new SpeechSynthesisUtterance(text);
      speech.lang = "en-US";
      try {
        speech.rate =
          Number(localStorage.getItem("vstep-speaking-voice-rate")) || 0.95;
      } catch {
        speech.rate = 0.95;
      }
      speech.onend = () => setSpeaking(false);
      speech.onerror = () => {
        setSpeaking(false);
        setTtsNotice(
          "Không mở được giọng đọc. Nội dung đề vẫn hiển thị đầy đủ.",
        );
      };
      window.speechSynthesis.speak(speech);
    };
    if (!session.tts_configured) {
      fallback();
      return;
    }
    try {
      const blob = await audioBlob(`/speaking/sessions/${session.id}/tts`, {
        method: "POST",
      });
      if (epoch !== ttsEpoch.current) return;
      ttsUrl.current = URL.createObjectURL(blob);
      tts.current = new Audio(ttsUrl.current);
      tts.current.onended = () => setSpeaking(false);
      await tts.current.play();
    } catch {
      if (epoch === ttsEpoch.current) {
        setTtsNotice("Đang dùng giọng đọc của trình duyệt.");
        fallback();
      }
    }
  }
  const status =
    busy ||
    (recording
      ? "Đang ghi âm"
      : hasAudio && !pending
        ? "Đã lưu bản ghi"
        : pending
          ? "Đã hoàn thành bản ghi"
          : recorder.state === "ready"
            ? "Sẵn sàng"
            : "Chưa cấp quyền microphone");
  return (
    <div className="space-y-5">
      <section className="panel overflow-hidden">
        <div className="flex items-center justify-between gap-3 border-b border-stone-100 px-6 py-4">
          <span className="flex items-center gap-2 text-sm font-semibold">
            <span className="flex size-8 items-center justify-center rounded-full bg-teal-50 text-teal-800">
              <AudioLines size={17} />
            </span>
            Giám khảo AI
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={listen}
            disabled={recording || !!busy}
          >
            <Volume2 />
            {speaking ? "Dừng đọc" : "Nghe câu hỏi"}
          </Button>
        </div>
        <div className="p-6 sm:p-9">
          <p className="eyebrow">
            {question.kind === "follow_up"
              ? "Follow-up question"
              : topics[question.topic] || question.topic}{" "}
            · Part {question.part}
          </p>
          {question.situation && (
            <p className="mt-5 text-lg leading-8 sm:text-xl">
              {question.situation}
            </p>
          )}
          <h1 className="mt-4 text-2xl font-semibold leading-relaxed sm:text-3xl">
            {question.question_text}
          </h1>
          <p className="mt-3 text-xs text-stone-500">
            Thời lượng tham khảo cho Part {question.part}:{" "}
            {Math.round(
              (session.part_timings?.[String(question.part)] || 0) / 60,
            )}{" "}
            phút (thiết lập của ứng dụng).
          </p>
          {!!question.options.length && (
            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              {question.options.map((option, i) => (
                <div
                  key={option}
                  className="rounded-xl border border-teal-100 bg-teal-50/50 p-5"
                >
                  <p className="mb-3 text-xs font-bold text-teal-700">
                    OPTION {String.fromCharCode(65 + i)}
                  </p>
                  <p className="text-sm leading-6">{option}</p>
                </div>
              ))}
            </div>
          )}
          {!!question.suggested_ideas.length && (
            <div className="mt-6">
              <IdeaMap
                topic={question.question_text}
                ideas={question.suggested_ideas}
              />
              <p className="mt-4 text-xs text-stone-500">
                Câu hỏi follow-up xuất hiện sau khi bạn hoàn thành bài nói
                chính.
              </p>
            </div>
          )}
          {ttsNotice && (
            <p role="status" className="mt-4 text-xs text-stone-500">
              {ttsNotice}
            </p>
          )}
        </div>
      </section>
      <section className="panel p-6 text-center sm:p-8">
        <p
          className={`flex items-center justify-center gap-2 text-sm font-medium ${recording ? "text-red-600" : "text-stone-500"}`}
          role="status"
        >
          {recording ? (
            <span className="size-2 animate-pulse rounded-full bg-red-500" />
          ) : hasAudio ? (
            <Check size={16} className="text-teal-700" />
          ) : (
            <MicOff size={16} />
          )}
          {status}
        </p>
        <div
          className="mx-auto mt-4 flex h-20 max-w-sm items-center justify-center gap-1.5"
          aria-label={
            recording ? "Mức âm thanh microphone" : "Microphone chưa ghi âm"
          }
        >
          {Array.from({ length: 37 }, (_, i) => (
            <span
              key={i}
              className={`w-1.5 rounded-full transition-all duration-75 ${recording ? "bg-teal-600" : "bg-stone-200"}`}
              style={{
                height: recording
                  ? `${8 + recorder.level * (30 + 36 * Math.abs(Math.sin(i * 1.2)))}px`
                  : `${8 + 12 * Math.abs(Math.sin(i * 0.7))}px`,
              }}
            />
          ))}
        </div>
        <p className="mt-2 text-3xl font-semibold tabular-nums">
          {duration(
            recorder.seconds || (answer?.audio_duration_ms || 0) / 1000,
          )}
        </p>
        <p className="mt-2 text-xs text-stone-400">
          Tối đa {duration(session.limits.max_audio_seconds)} / câu ·{" "}
          {session.limits.max_audio_mb} MB
        </p>
        {(error || recorder.error) && (
          <div className="text-left">
            <ErrorNotice message={error || recorder.error} />
          </div>
        )}
        {recorder.notice && (
          <p
            className="mx-auto mt-4 max-w-xl text-sm leading-6 text-amber-800"
            role="status"
          >
            {recorder.notice}
          </p>
        )}
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          {recording ? (
            <Button variant="destructive" onClick={stop} disabled={!!busy}>
              <Square />
              Dừng trả lời
            </Button>
          ) : (
            <>
              {!pending && !hasAudio && (
                <Button
                  size="lg"
                  disabled={!!busy || recorder.recovering}
                  onClick={start}
                >
                  <Mic />
                  {recorder.recovering
                    ? "Đang khôi phục..."
                    : "Bắt đầu trả lời"}
                </Button>
              )}
              {pending && (
                <Button
                  disabled={!!busy}
                  onClick={() =>
                    exclusive("Đang tải bản ghi...", async () => {
                      await upload(recorder.blob!);
                    })
                  }
                >
                  {error ? "Tải lại bản ghi" : "Gửi bản ghi"}
                </Button>
              )}
              {!full && (pending || hasAudio) && (
                <Button
                  variant="outline"
                  disabled={!!busy}
                  onClick={async () => {
                    await recorder.discard();
                    await start();
                  }}
                >
                  Thu lại
                </Button>
              )}
              {hasAudio && !pending && (
                <Button disabled={!!busy} onClick={() => next()}>
                  {question.sequence_number === session.total_questions - 1
                    ? "Hoàn thành bài nói"
                    : question.kind === "main_talk"
                      ? "Sang câu hỏi follow-up"
                      : "Câu tiếp theo"}{" "}
                  →
                </Button>
              )}
            </>
          )}
        </div>
        {!full && recorder.url && (
          <audio
            controls
            src={recorder.url}
            className="mx-auto mt-6 w-full max-w-lg"
            aria-label="Nghe thử bản ghi"
          />
        )}
        {!full && !recording && hasAudio && !pending && answer && (
          <div className="mx-auto mt-6 max-w-lg">
            <AudioPlayer key={answer.audio_duration_ms} answerId={answer.id} />
          </div>
        )}
        <p className="mt-5 text-xs leading-6 text-stone-500">
          {full
            ? "Mỗi câu chỉ nhận một bản ghi. Audio và phản hồi sẽ mở sau khi bạn hoàn thành bài thi."
            : "Bạn có thể nghe lại và thu lại trước khi chuyển câu. Bản ghi được gửi đi sẽ được lưu trong lịch sử."}
        </p>
      </section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          variant="ghost"
          onClick={leave}
          disabled={!!busy || recorder.recovering}
        >
          Lưu và thoát
        </Button>
        {!recording && !hasAudio && (
          <Button
            variant="ghost"
            disabled={!!busy || recorder.recovering}
            onClick={() => next(true)}
          >
            {pending ? "Bỏ qua bản ghi và câu này →" : "Bỏ qua câu này →"}
          </Button>
        )}
      </div>
    </div>
  );
}
