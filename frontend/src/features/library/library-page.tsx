"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, Plus, Star, Copy, Pencil, FolderOpen } from "lucide-react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api, post } from "@/services/api";
import { LibraryPracticeButton } from "./practice-link";
import {
  partLabels,
  parts,
  skillLabels,
  type Collection,
  type LibraryPart,
  type LibraryRow,
  type Skill,
} from "./types";
export function LibraryPage() {
  return (
    <RequireAuth>
      <LibraryList />
    </RequireAuth>
  );
}
function LibraryList() {
  const [filters, setFilters] = useState({
    skill: "",
    part: "",
    search: "",
    topic: "",
    tag: "",
    practiced: "",
    favorite: "",
    collection_id: "",
    order: "newest",
  });
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<{
    items: LibraryRow[];
    total: number;
  } | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [refresh, setRefresh] = useState(0);
  const load = useCallback(
    async (signal: AbortSignal) => {
      setLoading(true);
      setError("");
      try {
        const query = new URLSearchParams(
          Object.entries(filters).filter(([, v]) => v),
        );
        query.set("offset", String(offset));
        const result = await api<{ items: LibraryRow[]; total: number }>(
          `/my-questions?${query}`,
          { signal },
        );
        if (!signal.aborted) setData(result);
      } catch (e) {
        if (!signal.aborted) setError((e as Error).message);
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    },
    [filters, offset],
  );
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => void load(controller.signal), 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [load, refresh]);
  useEffect(() => {
    api<Collection[]>("/my-questions/collections")
      .then(setCollections)
      .catch((e) => setError(e.message));
  }, []);
  const filter = (key: keyof typeof filters, value: string) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      ...(key === "skill" ? { part: "" } : {}),
    }));
    setOffset(0);
  };
  async function action(
    id: string,
    kind: "favorite" | "duplicate",
    favorite?: boolean,
  ) {
    setBusy(id);
    setError("");
    setNotice("");
    try {
      if (kind === "duplicate") {
        await post(`/my-questions/${id}/duplicate`);
        setNotice("Đã tạo một bản sao trong thư viện.");
      } else
        await api(`/my-questions/${id}`, {
          method: "PATCH",
          body: JSON.stringify({ favorite }),
        });
      setRefresh((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <div className="space-y-7">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="eyebrow">My Question Library</p>
          <h1 className="mt-2 text-3xl font-semibold">Đề của tôi</h1>
          <p className="mt-3 max-w-2xl text-stone-500">
            Giữ những đề bạn muốn luyện lại. Dán văn bản, nhập ảnh/PDF hoặc tự
            tạo đề; Writing, Speaking và Reading đều ở đây.
          </p>
        </div>
        <Button asChild>
          <Link href="/my-questions/new">
            <Plus size={17} />
            Thêm đề
          </Link>
        </Button>
      </header>
      <section className="panel space-y-4 p-5">
        <div className="flex flex-wrap gap-2">
          {[["", "Tất cả kỹ năng"], ...Object.entries(skillLabels)].map(
            ([key, label]) => (
              <Button
                key={key}
                size="sm"
                variant={filters.skill === key ? "default" : "outline"}
                onClick={() => filter("skill", key)}
              >
                {label}
              </Button>
            ),
          )}
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <input
            className="field"
            aria-label="Tìm đề"
            placeholder="Tìm tên đề, nguồn, ghi chú…"
            value={filters.search}
            onChange={(e) => filter("search", e.target.value)}
          />
          <select
            className="field"
            aria-label="Phần thi"
            value={filters.part}
            onChange={(e) => filter("part", e.target.value)}
          >
            <option value="">Tất cả phần thi</option>
            {(filters.skill
              ? parts[filters.skill as Skill]
              : (Object.keys(partLabels) as LibraryPart[])
            ).map((part) => (
              <option key={part} value={part}>
                {partLabels[part]}
              </option>
            ))}
          </select>
          <input
            className="field"
            aria-label="Chủ đề"
            placeholder="Chủ đề, ví dụ: travel"
            value={filters.topic}
            onChange={(e) => filter("topic", e.target.value)}
          />
          <input
            className="field"
            aria-label="Tag"
            placeholder="Lọc theo tag"
            value={filters.tag}
            onChange={(e) => filter("tag", e.target.value)}
          />
          <select
            className="field"
            aria-label="Bộ sưu tập"
            value={filters.collection_id}
            onChange={(e) => filter("collection_id", e.target.value)}
          >
            <option value="">Tất cả bộ sưu tập</option>
            {collections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            className="field"
            aria-label="Trạng thái luyện"
            value={filters.practiced}
            onChange={(e) => filter("practiced", e.target.value)}
          >
            <option value="">Đã luyện & chưa luyện</option>
            <option value="true">Đã luyện</option>
            <option value="false">Chưa luyện</option>
          </select>
          <select
            className="field"
            aria-label="Thứ tự"
            value={filters.order}
            onChange={(e) => filter("order", e.target.value)}
          >
            <option value="newest">Mới nhất trước</option>
            <option value="oldest">Cũ nhất trước</option>
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={filters.favorite === "true"}
              onChange={(e) =>
                filter("favorite", e.target.checked ? "true" : "")
              }
            />
            <Star size={16} />
            Chỉ đề yêu thích
          </label>
        </div>
      </section>
      {error && <ErrorNotice message={error} />}{" "}
      {notice && (
        <p role="status" className="text-sm text-teal-800">
          {notice}
        </p>
      )}
      {loading ? (
        <Loading text="Đang mở thư viện…" />
      ) : data?.items.length ? (
        <>
          <p className="text-sm text-stone-500">
            {data.total} đề · Thư viện riêng của bạn
          </p>
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {data.items.map((row) => (
              <article key={row.id} className="panel flex flex-col gap-4 p-5">
                <div className="flex items-center justify-between">
                  <p className="eyebrow">
                    {skillLabels[row.document.skill]} ·{" "}
                    {partLabels[row.document.part]}
                  </p>
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label={
                      row.document.favorite ? "Bỏ yêu thích" : "Yêu thích"
                    }
                    disabled={busy === row.id}
                    onClick={() =>
                      action(row.id, "favorite", !row.document.favorite)
                    }
                  >
                    <Star
                      size={18}
                      className={
                        row.document.favorite
                          ? "fill-amber-400 text-amber-500"
                          : "text-stone-400"
                      }
                    />
                  </Button>
                </div>
                <Link
                  className="text-lg font-semibold hover:text-teal-800"
                  href={`/my-questions/${row.id}`}
                >
                  {row.document.title}
                </Link>
                <div className="space-y-1 text-xs text-stone-500">
                  <p>
                    {row.origin === "MANUAL"
                      ? "Tự nhập"
                      : "Đề nhập từ nguồn ngoài"}{" "}
                    · {row.document.topic} ·{" "}
                    {new Date(row.created_at).toLocaleDateString("vi-VN")}
                  </p>
                  {row.document.source_name && (
                    <p>Nguồn: {row.document.source_name}</p>
                  )}
                  {row.document.collection_id && (
                    <p className="flex items-center gap-1">
                      <FolderOpen size={12} />
                      {
                        collections.find(
                          (c) => c.id === row.document.collection_id,
                        )?.name
                      }
                    </p>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {row.document.tags.map((tag) => (
                    <button
                      key={tag}
                      className="rounded-md bg-stone-100 px-2 py-1 text-xs text-stone-600"
                      onClick={() => filter("tag", tag)}
                    >
                      #{tag}
                    </button>
                  ))}
                </div>
                {row.practice_issues.length > 0 && (
                  <p className="rounded-lg bg-amber-50 p-2 text-xs text-amber-900">
                    Bản nháp · Cần bổ sung nội dung trước khi luyện.
                  </p>
                )}
                {row.document.skill === "reading" &&
                  !row.answer_key.complete && (
                    <p className="text-xs text-amber-800">
                      Đáp án chưa đủ · {row.answer_key.trusted}/
                      {row.answer_key.total} câu
                    </p>
                  )}
                <div className="mt-auto border-t border-stone-100 pt-4 text-xs text-stone-500">
                  <p>
                    {row.stats.attempt_count
                      ? `${row.stats.attempt_count} lượt luyện`
                      : "Chưa luyện"}
                    {row.stats.last_practiced &&
                      ` · Gần nhất ${new Date(row.stats.last_practiced).toLocaleDateString("vi-VN")}`}
                  </p>
                  <p className="mt-1">
                    Điểm gần nhất: {row.stats.latest_score?.toFixed(2) ?? "—"} ·
                    Tốt nhất: {row.stats.best_score?.toFixed(2) ?? "—"}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <LibraryPracticeButton
                    id={row.id}
                    disabled={row.practice_issues.length > 0}
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    asChild
                    aria-label="Mở và sửa đề"
                  >
                    <Link href={`/my-questions/${row.id}`}>
                      <Pencil size={16} />
                    </Link>
                  </Button>
                  <Button
                    variant="outline"
                    size="icon"
                    aria-label="Nhân bản đề"
                    disabled={busy === row.id}
                    onClick={() => action(row.id, "duplicate")}
                  >
                    <Copy size={16} />
                  </Button>
                </div>
              </article>
            ))}
          </div>
          <div className="flex items-center justify-center gap-4">
            <Button
              variant="outline"
              disabled={!offset}
              onClick={() => setOffset((n) => Math.max(0, n - 24))}
            >
              Trước
            </Button>
            <span className="text-sm">
              {offset + 1}–{Math.min(offset + 24, data.total)} / {data.total}
            </span>
            <Button
              variant="outline"
              disabled={offset + 24 >= data.total}
              onClick={() => setOffset((n) => n + 24)}
            >
              Tiếp
            </Button>
          </div>
        </>
      ) : (
        <section className="panel py-16 text-center">
          <BookOpen className="mx-auto mb-4 text-teal-700" size={36} />
          <h2 className="text-xl font-semibold">Chưa có đề phù hợp</h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-stone-500">
            Thêm đề đầu tiên hoặc thay đổi bộ lọc để tìm đề đã lưu.
          </p>
          <Button className="mt-6" asChild>
            <Link href="/my-questions/new">Thêm đề vào thư viện</Link>
          </Button>
        </section>
      )}
    </div>
  );
}
