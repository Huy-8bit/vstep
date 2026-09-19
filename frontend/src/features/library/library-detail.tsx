"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api, ApiError, post } from "@/services/api";
import { DocumentForm } from "./document-form";
import { DocumentPreview } from "./document-preview";
import { normalizedDocument } from "./import-wizard";
import { LibraryPracticeButton } from "./practice-link";
import type { Collection, LibraryDocument, LibraryRow } from "./types";
export function LibraryDetail({ id }: { id: string }) {
  return (
    <RequireAuth>
      <Detail id={id} />
    </RequireAuth>
  );
}
function Detail({ id }: { id: string }) {
  const router = useRouter();
  const [row, setRow] = useState<LibraryRow | null>(null);
  const [document, setDocument] = useState<LibraryDocument | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [editing, setEditing] = useState(false);
  const [timed, setTimed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [duplicate, setDuplicate] = useState<{
    id: string;
    title: string;
  } | null>(null);
  useEffect(() => {
    let alive = true;
    Promise.all([
      api<LibraryRow>(`/my-questions/${id}`),
      api<Collection[]>("/my-questions/collections"),
    ])
      .then(([r, c]) => {
        if (alive) {
          setRow(r);
          setDocument(r.document);
          setCollections(c);
        }
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, [id]);
  async function save(force = false) {
    if (!document || !row) return;
    setBusy(true);
    setError("");
    setDuplicate(null);
    try {
      const result = await api<LibraryRow>(`/my-questions/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          document: normalizedDocument(document),
          expected_revision: row.revision,
          save_duplicate: force,
        }),
      });
      setRow({ ...result, stats: row.stats });
      setDocument(result.document);
      setEditing(false);
      setNotice("Đã lưu phiên bản mới. Các lượt luyện trước vẫn giữ nguyên.");
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && e.code === "duplicate_question")
        setDuplicate(e.details.duplicate as { id: string; title: string });
    } finally {
      setBusy(false);
    }
  }
  if (!row || !document)
    return error ? (
      <>
        <ErrorNotice message={error} />
        <Button asChild variant="outline">
          <Link href="/my-questions">Về thư viện</Link>
        </Button>
      </>
    ) : (
      <Loading text="Đang mở đề…" />
    );
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/my-questions" className="text-sm text-teal-800">
        ← Đề của tôi
      </Link>
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">
            {editing ? "Chỉnh sửa đề" : row.document.title}
          </h1>
          <p className="mt-2 text-sm text-stone-500">
            Phiên bản {row.revision} · {row.stats.attempt_count} lượt luyện ·
            Tốt nhất {row.stats.best_score?.toFixed(2) ?? "—"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => {
              setEditing(!editing);
              setDocument(row.document);
              setNotice("");
              setError("");
            }}
          >
            {editing ? "Hủy chỉnh sửa" : "Sửa đề / đặt đáp án"}
          </Button>
          <Button
            variant="outline"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                const copy = await post<LibraryRow>(
                  `/my-questions/${id}/duplicate`,
                );
                router.push(`/my-questions/${copy.id}`);
              } catch (e) {
                setError((e as Error).message);
              } finally {
                setBusy(false);
              }
            }}
          >
            Nhân bản
          </Button>
        </div>
      </header>
      {notice && (
        <p
          role="status"
          className="rounded-lg bg-teal-50 p-3 text-sm text-teal-900"
        >
          {notice}
        </p>
      )}
      {error && <ErrorNotice message={error} />}
      {editing ? (
        <section className="panel p-5 sm:p-7">
          <DocumentForm
            value={document}
            onChange={setDocument}
            collections={collections}
            onCollection={(c) => setCollections((prev) => [...prev, c])}
          />
          <Button className="mt-6" disabled={busy} onClick={() => save()}>
            {busy ? "Đang lưu…" : "Lưu đề"}
          </Button>
          {duplicate && (
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                href={`/my-questions/${duplicate.id}`}
                target="_blank"
                className="text-sm text-teal-800 underline"
              >
                Xem đề trùng: {duplicate.title}
              </Link>
              <Button
                variant="outline"
                disabled={busy}
                onClick={() => save(true)}
              >
                Vẫn lưu
              </Button>
            </div>
          )}
        </section>
      ) : (
        <>
          <section className="panel p-5 sm:p-7">
            <DocumentPreview value={row.document} />
            {row.document.source_name && (
              <p className="mt-5 text-sm text-stone-500">
                Nguồn: {row.document.source_name}
              </p>
            )}
            {row.document.source_url && (
              <a
                href={row.document.source_url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 block text-sm text-teal-800 underline"
              >
                Mở nguồn tham khảo
              </a>
            )}
            {row.document.notes && (
              <p className="mt-4 whitespace-pre-wrap text-sm text-stone-600">
                Ghi chú: {row.document.notes}
              </p>
            )}
          </section>
          <section className="panel space-y-4 p-5">
            {row.practice_issues.map((issue, i) => (
              <p key={i} className="text-sm text-amber-800">
                {issue}
              </p>
            ))}
            {!row.answer_key.complete && row.document.skill === "reading" && (
              <p className="text-sm text-amber-800">
                Chưa đủ đáp án ({row.answer_key.trusted}/{row.answer_key.total}
                ). Bạn vẫn có thể luyện và xem lại bài; chưa có điểm chính xác
                cho toàn đề.
              </p>
            )}
            <p className="text-sm text-stone-500">
              Lượt luyện dùng nguyên đề đã lưu và cùng hệ thống chấm, Vocabulary
              Coach, lịch sử và tiến độ hiện có.
            </p>
            {row.document.part !== "full" && (
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={timed}
                  onChange={(e) => setTimed(e.target.checked)}
                />
                Bật giới hạn thời gian
              </label>
            )}
            <LibraryPracticeButton
              id={id}
              timed={timed}
              disabled={!!row.practice_issues.length}
            />
          </section>
        </>
      )}
      <div className="flex flex-wrap items-center gap-3 border-t border-stone-200 pt-5">
        {deleting ? (
          <>
            <p className="text-sm text-stone-500">
              Xóa khỏi thư viện? Lịch sử luyện vẫn được giữ.
            </p>
            <Button
              variant="outline"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await api(`/my-questions/${id}`, { method: "DELETE" });
                  router.push("/my-questions");
                } catch (e) {
                  setError((e as Error).message);
                  setBusy(false);
                }
              }}
            >
              Xóa đề
            </Button>
            <Button variant="ghost" onClick={() => setDeleting(false)}>
              Giữ lại
            </Button>
          </>
        ) : (
          <Button variant="ghost" onClick={() => setDeleting(true)}>
            Xóa khỏi thư viện
          </Button>
        )}
      </div>
    </div>
  );
}
