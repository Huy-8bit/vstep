"use client";
import { useEffect, useRef, useState } from "react";
import { audioBlob } from "@/services/api";
import { Button } from "@/components/ui/button";
export function AudioPlayer({
  answerId,
  path,
  method = "GET",
  label = "Nghe lại bản ghi",
  disabled = false,
}: {
  answerId?: string;
  path?: string;
  method?: "GET" | "POST";
  label?: string;
  disabled?: boolean;
}) {
  const player = useRef<HTMLAudioElement>(null);
  useEffect(() => {
    if (disabled) player.current?.pause();
  }, [disabled]);
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [url]);
  async function load() {
    setLoading(true);
    setError("");
    try {
      const blob = await audioBlob(
        path || `/speaking/answers/${answerId}/audio`,
        { method },
      );
      setUrl(URL.createObjectURL(blob));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="space-y-2">
      {url ? (
        <audio
          ref={player}
          onPlay={() => {
            if (disabled) player.current?.pause();
          }}
          className="w-full"
          controls
          src={url}
          preload="metadata"
          aria-label={label}
        />
      ) : (
        <Button
          variant="outline"
          size="sm"
          disabled={loading || disabled}
          onClick={load}
        >
          {loading ? "Đang mở âm thanh..." : label}
        </Button>
      )}
      {error && (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
