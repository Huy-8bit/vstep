"use client";
import { useEffect, useState } from "react";
import { audioBlob } from "@/services/api";
import { Button } from "@/components/ui/button";
export function AudioPlayer({ answerId }: { answerId: string }) {
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
      const blob = await audioBlob(`/speaking/answers/${answerId}/audio`);
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
          className="w-full"
          controls
          src={url}
          preload="metadata"
          aria-label="Nghe lại câu trả lời"
        />
      ) : (
        <Button variant="outline" size="sm" disabled={loading} onClick={load}>
          {loading ? "Đang mở bản ghi..." : "Nghe lại bản ghi"}
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
