"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { loadTake, removeTake, saveTake } from "./recording-store";

export function useRecorder(key: string, maxSeconds: number, maxMb: number) {
  const [state, setState] = useState<"idle" | "ready" | "recording" | "done">(
    "idle",
  );
  const [seconds, setSeconds] = useState(0);
  const [level, setLevel] = useState(0);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [recovering, setRecovering] = useState(true);
  const [url, setUrl] = useState("");
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const context = useRef<AudioContext | null>(null);
  const started = useRef(0);
  const secondsRef = useRef(0);
  const alive = useRef(true);
  const writing = useRef<Promise<void>>(Promise.resolve());
  const frame = useRef(0);
  const clock = useRef<ReturnType<typeof setInterval> | null>(null);
  const stopPromise = useRef<Promise<Blob | null> | null>(null);
  const resolveStop = useRef<((blob: Blob | null) => void) | null>(null);
  const release = useCallback(() => {
    if (clock.current) clearInterval(clock.current);
    cancelAnimationFrame(frame.current);
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
    if (context.current && context.current.state !== "closed")
      void context.current.close();
    context.current = null;
    if (alive.current) setLevel(0);
  }, []);
  const persist = useCallback(
    (take: Blob, elapsed: number) => {
      writing.current = writing.current
        .then(() =>
          saveTake({ key, blob: take, duration: elapsed, updated: Date.now() }),
        )
        .catch(() => {
          if (alive.current)
            setNotice(
              "Trình duyệt không lưu được bản dự phòng. Bản ghi vẫn ở trang này; hãy tải lên trước khi đóng trang.",
            );
        });
    },
    [key],
  );
  useEffect(() => {
    alive.current = true;
    let cancelled = false;
    loadTake(key)
      .then((take) => {
        if (!cancelled && take) {
          setBlob(take.blob);
          setSeconds(take.duration);
          setState("done");
          setNotice(
            "Đã khôi phục bản ghi chưa tải lên. Bạn có thể tiếp tục tải bản ghi này.",
          );
        }
      })
      .catch(() => {
        if (!cancelled)
          setNotice("Bản ghi tạm sẽ được giữ trong trang này nếu tải lên lỗi.");
      })
      .finally(() => {
        if (!cancelled) setRecovering(false);
      });
    return () => {
      cancelled = true;
      alive.current = false;
      if (recorder.current?.state === "recording") recorder.current.stop();
      else release();
    };
  }, [key, release]);
  useEffect(() => {
    if (!blob) {
      setUrl("");
      return;
    }
    const objectUrl = URL.createObjectURL(blob);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [blob]);
  const stop = useCallback(async () => {
    if (recorder.current?.state === "recording") recorder.current.stop();
    return stopPromise.current ? await stopPromise.current : null;
  }, []);
  const start = useCallback(
    async (beforeRecord: () => Promise<void>) => {
      setError("");
      if (
        !navigator.mediaDevices?.getUserMedia ||
        typeof MediaRecorder === "undefined"
      ) {
        setError(
          "Trình duyệt chưa hỗ trợ ghi âm. Hãy dùng Chrome, Edge, Firefox hoặc Safari phiên bản mới trên HTTPS hoặc localhost.",
        );
        return;
      }
      try {
        stream.current = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        if (!alive.current) {
          release();
          return;
        }
        setState("ready");
        await beforeRecord();
        if (!alive.current) {
          release();
          return;
        }
        const mime = [
          "audio/webm;codecs=opus",
          "audio/mp4",
          "audio/ogg;codecs=opus",
          "audio/webm",
        ].find((type) => MediaRecorder.isTypeSupported(type));
        const media = new MediaRecorder(
          stream.current,
          mime ? { mimeType: mime, audioBitsPerSecond: 96000 } : undefined,
        );
        const chunks: Blob[] = [];
        let bytes = 0;
        recorder.current = media;
        stopPromise.current = new Promise((resolve) => {
          resolveStop.current = resolve;
        });
        const type = media.mimeType || mime || "audio/webm";
        media.ondataavailable = (event) => {
          if (!event.data.size) return;
          chunks.push(event.data);
          bytes += event.data.size;
          const snapshot = new Blob(chunks, { type });
          persist(
            snapshot,
            Math.min(maxSeconds, (Date.now() - started.current) / 1000),
          );
          if (
            bytes >= maxMb * 1024 * 1024 * 0.95 &&
            media.state === "recording"
          ) {
            if (alive.current)
              setNotice(
                "Đã đạt giới hạn kích thước bản ghi. Hãy tải lên để tiếp tục.",
              );
            media.stop();
          }
        };
        media.onstop = () => {
          const take = chunks.length ? new Blob(chunks, { type }) : null;
          const elapsed = Math.min(
            maxSeconds,
            (Date.now() - started.current) / 1000,
          );
          release();
          if (take) persist(take, elapsed);
          if (alive.current) {
            setBlob(take);
            setSeconds(elapsed);
            setState(take ? "done" : "idle");
            if (!take)
              setError(
                "Chưa nhận được âm thanh. Kiểm tra microphone và thử lại.",
              );
          }
          resolveStop.current?.(take);
        };
        media.onerror = () => {
          if (alive.current)
            setError(
              "Ghi âm bị gián đoạn. Hãy tải phần đã ghi hoặc kiểm tra microphone.",
            );
          if (media.state === "recording") media.stop();
        };
        stream.current.getAudioTracks().forEach(
          (track) =>
            (track.onended = () => {
              if (media.state === "recording") media.stop();
            }),
        );
        setBlob(null);
        setNotice("");
        setSeconds(0);
        secondsRef.current = 0;
        started.current = Date.now();
        media.start(3000);
        setState("recording");
        clock.current = setInterval(() => {
          const elapsed = (Date.now() - started.current) / 1000;
          secondsRef.current = elapsed;
          if (alive.current) setSeconds(elapsed);
          if (elapsed >= maxSeconds - 1 && media.state === "recording") {
            setNotice(
              "Đã đạt thời lượng tối đa cho một câu. Bản ghi đã được giữ lại.",
            );
            media.stop();
          }
        }, 250);
        // A live input meter is optional; a Web Audio limitation must never prevent recording.
        try {
          const audio = new AudioContext();
          context.current = audio;
          void audio.resume().catch(() => {});
          const analyser = audio.createAnalyser();
          analyser.fftSize = 256;
          audio.createMediaStreamSource(stream.current).connect(analyser);
          const values = new Uint8Array(analyser.fftSize);
          const draw = () => {
            if (media.state !== "recording") return;
            analyser.getByteTimeDomainData(values);
            const energy = Math.sqrt(
              values.reduce(
                (sum, value) => sum + ((value - 128) / 128) ** 2,
                0,
              ) / values.length,
            );
            if (alive.current) setLevel(Math.min(1, energy * 7));
            frame.current = requestAnimationFrame(draw);
          };
          draw();
        } catch {
          /* Recorder remains active without a meter. */
        }
      } catch (e) {
        release();
        if (alive.current) {
          setState("idle");
          const name = e instanceof DOMException ? e.name : "";
          setError(
            name === "NotAllowedError"
              ? "Bạn chưa cho phép microphone. Bấm biểu tượng ổ khóa cạnh địa chỉ trang, cho phép Microphone rồi thử lại. Trên điện thoại, kiểm tra thêm quyền microphone của trình duyệt trong Cài đặt."
              : name === "NotFoundError"
                ? "Không tìm thấy microphone. Hãy kết nối thiết bị thu âm rồi thử lại."
                : name === "NotReadableError"
                  ? "Microphone đang bận hoặc không truy cập được. Đóng ứng dụng đang dùng microphone rồi thử lại."
                  : (e as Error).message || "Không thể bắt đầu ghi âm.",
          );
        }
      }
    },
    [maxMb, maxSeconds, persist, release],
  );
  const discard = useCallback(async () => {
    await writing.current;
    await removeTake(key).catch(() => {});
    setBlob(null);
    setSeconds(0);
    setState("idle");
    setNotice("");
  }, [key]);
  return {
    state,
    seconds,
    level,
    blob,
    url,
    error,
    notice,
    recovering,
    start,
    stop,
    discard,
    flush: () => writing.current,
  };
}
