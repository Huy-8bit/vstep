"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
import { api } from "@/services/api";
function PracticeAsset({ id }: { id: string }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    api<Blob>(`/my-questions/assets/${id}`, {}, true, true)
      .then((blob) => {
        if (active && blob.type.startsWith("image/")) {
          objectUrl = URL.createObjectURL(blob);
          setUrl(objectUrl);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [id]);
  return (
    <div className="space-y-2">
      {url && (
        <Image
          unoptimized
          width={1600}
          height={1200}
          src={url}
          alt="Ảnh đề gốc do bạn chọn hiển thị"
          className="h-auto max-w-full rounded-lg"
        />
      )}
      <a
        href={`/api/v1/my-questions/assets/${id}`}
        target="_blank"
        rel="noreferrer"
        className="text-xs text-teal-800 underline"
      >
        Mở tệp đề gốc
      </a>
      {error && <p className="text-xs text-red-700">{error}</p>}
    </div>
  );
}
export function PracticeAssets({ ids }: { ids?: string[] }) {
  return ids?.length ? (
    <aside className="my-4 space-y-4 rounded-xl border border-stone-200 p-4">
      <p className="text-xs font-semibold text-stone-500">Tài liệu kèm đề</p>
      {ids.map((id) => (
        <PracticeAsset key={id} id={id} />
      ))}
    </aside>
  ) : null;
}
