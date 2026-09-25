"use client";
import { staticPageUrl } from "@/lib/static-page-url";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { post } from "@/services/api";
import type { LibraryMetadata } from "./types";
export function LibraryPracticeButton({
  id,
  revision,
  timed = false,
  label = "Luyện đề này",
  disabled = false,
}: {
  id: string;
  revision?: number | null;
  timed?: boolean;
  label?: string;
  disabled?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();
  return (
    <div className="space-y-2">
      <Button
        disabled={busy || disabled}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            const result = await post<{ url: string }>(
              `/my-questions/${id}/practice`,
              { revision: revision || null, timed },
            );
            router.push(staticPageUrl(result.url));
          } catch (e) {
            setError((e as Error).message);
            setBusy(false);
          }
        }}
      >
        {busy ? "Đang mở đề…" : label}
      </Button>
      {error && (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
export function LibraryOrigin({
  value,
  retry = false,
}: {
  value: LibraryMetadata;
  retry?: boolean;
}) {
  if (!value.library_question_id) return null;
  return (
    <div className="my-3 flex flex-wrap items-center gap-3">
      <Link
        href={`/my-questions/detail?id=${value.library_question_id}`}
        className="rounded-lg bg-teal-50 px-3 py-1.5 text-sm text-teal-900"
      >
        Đề của tôi · {value.library_title || "Đề đã nhập"} · v
        {value.library_revision}
      </Link>
      {retry && (
        <LibraryPracticeButton
          id={value.library_question_id}
          revision={value.library_revision}
          label="Luyện lại đúng đề này"
        />
      )}
    </div>
  );
}
