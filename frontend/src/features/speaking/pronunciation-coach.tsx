"use client";
import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Mic, Square, RotateCcw } from "lucide-react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Paywall } from "@/components/paywall";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api, post } from "@/services/api";
import { AudioPlayer } from "./audio-player";
import { AudioAssessmentPanel } from "./audio-assessment-panel";
import { useRecorder } from "./use-recorder";
import { duration, scoreText, disclaimer } from "./types";
import type { PronunciationPractice } from "./pronunciation-types";

type Config = {
  max_audio_mb: number;
  max_audio_seconds: number;
  audio_analysis_configured: boolean;
  ai_configured: boolean;
  tts_configured: boolean;
};
const endpoint = "/speaking/pronunciation/practices";
export function PronunciationCoach() {
  const params = useSearchParams();
  return (
    <RequireAuth>
      <PronunciationGate key={params.toString()} />
    </RequireAuth>
  );
}
function PronunciationGate() {
  const { user } = useAuth();
  if (user?.role !== "ADMIN" && user?.access?.tier !== "VIP") return <Paywall title="Luyện phát âm dành cho VIP" />;
  return <Coach />;
}
function Coach() {
  const params = useSearchParams();
  const [reference, setReference] = useState(
    params.get("reference")?.slice(0, 500) || "",
  );
  const [item, setItem] = useState<PronunciationPractice | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [historyVersion, setHistoryVersion] = useState(0);
  const creationId = useRef<string | null>(null);
  const creating = useRef(false);
  const id = params.get("id");
  useEffect(() => {
    let active = true;
    api<Config>("/speaking/config")
      .then((c) => {
        if (active) setConfig(c);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, []);
  useEffect(() => {
    let active = true;
    if (id) {
      api<PronunciationPractice>(`${endpoint}/${id}`)
        .then((result) => {
          if (active) {
            setItem(result);
            setReference(result.reference_text);
          }
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    }
    return () => {
      active = false;
    };
  }, [id]);
  async function create(repeat = false) {
    if (creating.current) return;
    creating.current = true;
    setBusy(true);
    setError("");
    try {
      creationId.current ||= crypto.randomUUID();
      const result = await post<PronunciationPractice>(endpoint, {
        reference_text: repeat && item ? item.reference_text : reference,
        source_answer_id: repeat
          ? item?.source_answer_id
          : params.get("source"),
        source_issue_type: repeat
          ? item?.source_issue_type
          : params.get("issue"),
        client_request_id: creationId.current,
      });
      creationId.current = null;
      setItem(result);
      setHistoryVersion((v) => v + 1);
      window.history.replaceState(
        null,
        "",
        `/speaking/pronunciation?id=${result.id}`,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      creating.current = false;
    }
  }
  return (
    <div className="space-y-7">
      <div>
        <Link className="text-xs text-stone-500" href="/speaking">
          ← Speaking
        </Link>
        <p className="eyebrow mt-6">Nghe · nói · điều chỉnh</p>
        <h1 className="mt-2 text-3xl font-bold">Luyện phát âm</h1>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-500">
          Chọn một từ hoặc câu, nghe mẫu rồi ghi âm. Luyện lại cùng nội dung để
          theo dõi sự thay đổi.
        </p>
      </div>
      {error && <ErrorNotice message={error} />}
      {!config && !error && <Loading text="Đang mở phòng luyện..." />}
      {config &&
        (!config.ai_configured || !config.audio_analysis_configured) && (
          <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">
            Phân tích audio chưa được bật trên máy chủ. Bạn vẫn có thể lưu bản
            ghi và xem lịch sử.
          </p>
        )}
      {!item && (
        <section className="panel p-6">
          <label className="block text-sm font-semibold" htmlFor="reference">
            Từ hoặc câu tiếng Anh
          </label>
          <textarea
            id="reference"
            className="field mt-3 min-h-28 w-full"
            lang="en"
            maxLength={500}
            value={reference}
            disabled={busy}
            placeholder="e.g. I enjoy learning about the environment."
            onChange={(e) => {
              setReference(e.target.value);
              creationId.current = null;
            }}
          />
          <p className="mt-2 text-xs text-stone-400">
            {reference.length}/500 ký tự
          </p>
          <Button
            className="mt-4"
            onClick={() => create()}
            disabled={busy || !config || !reference.trim()}
          >
            {busy ? "Đang lưu..." : "Bắt đầu luyện"}
          </Button>
        </section>
      )}
      {item && config && (
        <Practice
          key={item.id}
          item={item}
          config={config}
          onChange={(next) => {
            setItem(next);
            setHistoryVersion((v) => v + 1);
          }}
          onRepeat={() => create(true)}
          repeating={busy}
        />
      )}
      {item && (
        <Button asChild variant="outline">
          <Link href="/speaking/pronunciation">Chọn từ hoặc câu khác</Link>
        </Button>
      )}
      <PronunciationHistory
        key={item?.reference_hash || "all"}
        version={historyVersion}
        referenceHash={item?.reference_hash}
      />
      <p className="rounded-xl bg-stone-100 p-4 text-xs leading-6 text-stone-500">
        {disclaimer}
      </p>
    </div>
  );
}
function Practice({
  item,
  config,
  onChange,
  onRepeat,
  repeating,
}: {
  item: PronunciationPractice;
  config: Config;
  onChange: (item: PronunciationPractice) => void;
  onRepeat: () => void;
  repeating: boolean;
}) {
  const { user } = useAuth();
  const recorder = useRecorder(
    `pronunciation:${user!.id}:${item.id}`,
    Math.min(60, config.max_audio_seconds),
    config.max_audio_mb,
  );
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  const running = useRef(false);
  const recording =
    starting || recorder.state === "recording" || recorder.state === "ready";
  async function startRecording() {
    if (running.current) return;
    running.current = true;
    setStarting(true);
    try {
      await recorder.start(async () => {});
    } finally {
      setStarting(false);
      running.current = false;
    }
  }
  async function analyze() {
    if (running.current) return;
    running.current = true;
    setError("");
    try {
      let next = item;
      if (!item.audio_url) {
        if (!recorder.blob) return;
        setBusy("Đang lưu bản ghi...");
        await recorder.flush();
        const file = new FormData();
        file.append("file", recorder.blob, "pronunciation.webm");
        next = await api<PronunciationPractice>(
          `${endpoint}/${item.id}/audio`,
          { method: "POST", body: file },
        );
        onChange(next);
        await recorder.discard();
      }
      setBusy("AI đang nghe và phân tích phát âm...");
      next = await post<PronunciationPractice>(
        `${endpoint}/${item.id}/analyze`,
      );
      onChange(next);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
      running.current = false;
    }
  }
  return (
    <div className="space-y-5">
      <section className="panel space-y-5 p-6">
        <p className="eyebrow">Nội dung luyện</p>
        <p lang="en" className="text-xl font-semibold leading-9 text-teal-900">
          {item.reference_text}
        </p>
        <div className="rounded-xl bg-teal-50 p-4">
          <AudioPlayer
            path={`${endpoint}/${item.id}/tts`}
            method="POST"
            label="Nghe phát âm mẫu"
            disabled={recording || !!busy || !config.tts_configured}
          />
          <p className="mt-2 text-xs text-teal-800">
            Giọng đọc mẫu do AI tạo bằng OpenAI TTS.
          </p>
          {!config.tts_configured && (
            <p className="mt-2 text-xs text-amber-800">
              Máy chủ chưa cấu hình giọng đọc mẫu.
            </p>
          )}
        </div>
        {item.source_answer_id && (
          <div>
            <p className="mb-2 text-xs text-stone-500">
              Bản ghi trong bài Speaking
            </p>
            <AudioPlayer
              answerId={item.source_answer_id}
              disabled={recording}
            />
          </div>
        )}
        {error && <ErrorNotice message={error} />}
        {recorder.error && <ErrorNotice message={recorder.error} />}
        {busy && (
          <p role="status" className="text-sm text-teal-800">
            {busy} Bản ghi được giữ lại nếu cần thử tiếp.
          </p>
        )}
        {recorder.notice && !item.audio_url && (
          <p className="text-xs text-stone-500">{recorder.notice}</p>
        )}
        {!item.audio_url && (
          <div className="space-y-4">
            {recording && (
              <div role="status">
                <p className="text-lg font-semibold text-red-700">
                  Đang ghi · {duration(recorder.seconds)}
                </p>
                <div
                  aria-label="Mức âm thanh microphone"
                  className="mt-3 h-2 rounded bg-stone-100"
                >
                  <div
                    className="h-full rounded bg-teal-500"
                    style={{ width: `${recorder.level * 100}%` }}
                  />
                </div>
              </div>
            )}
            {recorder.url && (
              <audio
                controls
                src={recorder.url}
                className="w-full"
                aria-label="Bản luyện chưa tải lên"
              />
            )}
            <div className="flex flex-wrap gap-3">
              {recording ? (
                <Button
                  disabled={starting || recorder.state === "ready"}
                  onClick={() => recorder.stop()}
                >
                  <Square />
                  Dừng ghi
                </Button>
              ) : (
                <Button
                  disabled={!!busy || recorder.recovering || !!recorder.blob}
                  onClick={startRecording}
                >
                  <Mic />
                  Ghi âm
                </Button>
              )}
              {recorder.blob && !recording && (
                <>
                  <Button onClick={analyze} disabled={!!busy}>
                    Lưu và phân tích
                  </Button>
                  <Button
                    variant="outline"
                    disabled={!!busy}
                    onClick={recorder.discard}
                  >
                    Bỏ bản ghi tạm
                  </Button>
                </>
              )}
            </div>
            <p className="text-xs text-stone-400">
              Tối đa {Math.min(60, config.max_audio_seconds)} giây. Đọc đúng nội
              dung mẫu; dừng nghe mẫu trước khi nói.
            </p>
          </div>
        )}
        {item.audio_url && (
          <AudioPlayer
            path={`${endpoint}/${item.id}/audio`}
            label="Nghe lại lần luyện này"
          />
        )}
        {item.audio_url && !item.analysis && (
          <Button disabled={!!busy} onClick={analyze}>
            Phân tích bản ghi đã lưu
          </Button>
        )}
        {item.audio_url && (
          <Button
            variant="outline"
            onClick={onRepeat}
            disabled={!!busy || repeating}
          >
            <RotateCcw />
            {repeating ? "Đang mở lượt mới..." : "Luyện lại cùng nội dung"}
          </Button>
        )}
      </section>
      {item.analysis && (
        <AudioAssessmentPanel
          analysis={item.analysis}
          sourceAnswerId={item.source_answer_id || undefined}
          practice
        />
      )}
    </div>
  );
}
export function PronunciationHistory({
  version = 0,
  referenceHash,
}: {
  version?: number;
  referenceHash?: string;
}) {
  const [data, setData] = useState<{
    total: number;
    items: PronunciationPractice[];
  } | null>(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let active = true;
    api<{ total: number; items: PronunciationPractice[] }>(
      `/speaking/pronunciation/history?offset=${offset}${referenceHash ? `&reference_hash=${referenceHash}` : ""}`,
    )
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
  }, [offset, referenceHash, version, retry]);
  return (
    <section className="panel p-5 sm:p-7">
      <div className="flex flex-wrap justify-between gap-3">
        <h2 className="text-lg font-bold">
          {referenceHash
            ? "Các lần luyện cùng nội dung"
            : "Lịch sử luyện phát âm"}
        </h2>
        <Link href="/speaking/progress" className="text-sm text-teal-700">
          Xem tiến bộ →
        </Link>
      </div>
      {error && (
        <>
          <ErrorNotice message={error} />
          <Button
            onClick={() => setRetry((value) => value + 1)}
            variant="outline"
          >
            Thử tải lại
          </Button>
        </>
      )}
      {data && !data.total && (
        <p className="mt-4 text-sm text-stone-500">
          Chưa có lượt luyện. Bản ghi và điểm của bạn sẽ xuất hiện ở đây.
        </p>
      )}
      {!!data?.items.length && (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-stone-200 text-xs text-stone-500">
                <th className="p-3">Nội dung</th>
                <th className="p-3">Phát âm</th>
                <th className="p-3">Trôi chảy</th>
                <th className="p-3">Ngày luyện</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr key={item.id} className="border-b border-stone-100">
                  <td className="max-w-xs p-3">
                    <Link
                      className="font-medium text-teal-800 underline underline-offset-4"
                      href={`/speaking/pronunciation?id=${item.id}`}
                    >
                      {item.reference_text}
                    </Link>
                    <p className="mt-1 text-xs text-stone-400">
                      {item.status === "ANALYZED"
                        ? "Đã phân tích"
                        : item.audio_url
                          ? "Đã lưu audio"
                          : "Chưa ghi âm"}
                    </p>
                  </td>
                  <td className="p-3">{scoreText(item.pronunciation_score)}</td>
                  <td className="p-3">{scoreText(item.fluency_score)}</td>
                  <td className="whitespace-nowrap p-3 text-xs text-stone-500">
                    {new Date(item.created_at).toLocaleString("vi-VN")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && data.total > 20 && (
        <div className="mt-4 flex gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={!offset}
            onClick={() => setOffset(Math.max(0, offset - 20))}
          >
            Trước
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + 20 >= data.total}
            onClick={() => setOffset(offset + 20)}
          >
            Sau
          </Button>
        </div>
      )}
    </section>
  );
}
