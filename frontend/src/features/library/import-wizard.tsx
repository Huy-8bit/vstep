"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/auth-provider";
import { FileText, ImagePlus, PenLine } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, ApiError, post } from "@/services/api";
import { DocumentForm } from "./document-form";
import { DocumentPreview } from "./document-preview";
import { Field } from "./form-fields";
import {
  emptyDocument,
  partLabels,
  skillLabels,
  type Collection,
  type LibraryDocument,
  type LibraryRow,
  type ParsedImport,
  type ParsedItem,
} from "./types";

type Draft = ParsedItem & { selected: boolean; savedId?: string };
export function normalizedDocument(doc: LibraryDocument) {
  return {
    ...doc,
    title: doc.title.trim(),
    topic: doc.topic.trim() || "other",
    tags: [...new Set(doc.tags.map((v) => v.trim()).filter(Boolean))],
    source_url: doc.source_url || null,
  };
}
export function ImportWizard() {
  const router = useRouter();
  const { user } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  const [method, setMethod] = useState<"manual" | "paste" | "file">("paste");
  const [raw, setRaw] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [assetId, setAssetId] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [active, setActive] = useState(0);
  const [tab, setTab] = useState<"edit" | "preview">("preview");
  const [collections, setCollections] = useState<Collection[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [duplicate, setDuplicate] = useState<{
    index: number;
    id: string;
    title: string;
  } | null>(null);
  useEffect(() => {
    api<Collection[]>("/my-questions/collections")
      .then(setCollections)
      .catch((e) => setError(e.message));
  }, []);
  const update = (document: LibraryDocument) =>
    setDrafts((prev) =>
      prev.map((d, i) => (i === active ? { ...d, document } : d)),
    );
  async function analyze() {
    setError("");
    setWarnings([]);
    setBusy(
      method === "file"
        ? "Đang kiểm tra và tải tệp…"
        : "AI đang phân tích văn bản…",
    );
    try {
      let id = assetId;
      if (method === "file" && !id) {
        if (!file) throw new Error("Chọn ảnh hoặc PDF để nhập.");
        const form = new FormData();
        form.append("file", file);
        id = (
          await api<{ id: string }>("/my-questions/assets", {
            method: "POST",
            body: form,
          })
        ).id;
        setAssetId(id);
      }
      setBusy(
        "AI đang đọc và phân loại đề. Nội dung sẽ hiện để bạn kiểm tra trước khi lưu…",
      );
      const parsed = await post<ParsedImport>(
        "/my-questions/parse",
        method === "file" ? { asset_id: id } : { text: raw },
      );
      setDrafts(parsed.items.map((d) => ({ ...d, selected: true })));
      setWarnings(parsed.warnings);
      setActive(0);
      setTab("preview");
      if (!parsed.items.length)
        setError(
          "Chưa nhận diện được đề. Sửa văn bản, chọn ảnh rõ hơn hoặc nhập thủ công.",
        );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function save(forceIndex?: number) {
    setBusy("Đang lưu đề…");
    setError("");
    setDuplicate(null);
    const updated = [...drafts];
    let lastId = "";
    try {
      for (let i = 0; i < updated.length; i++) {
        if (!updated[i].selected || updated[i].savedId) continue;
        try {
          const row = await post<LibraryRow>("/my-questions", {
            document: normalizedDocument(updated[i].document),
            save_duplicate: forceIndex === i,
          });
          updated[i] = { ...updated[i], savedId: row.id };
          lastId = row.id;
          setDrafts([...updated]);
        } catch (e) {
          setActive(i);
          if (e instanceof ApiError && e.code === "duplicate_question") {
            const match = e.details.duplicate as { id: string; title: string };
            setDuplicate({ index: i, ...match });
          }
          throw e;
        }
      }
      if (updated.filter((d) => d.selected).every((d) => d.savedId))
        router.push(
          updated.filter((d) => d.selected).length === 1
            ? `/my-questions/detail?id=${lastId || updated.find((d) => d.selected)?.savedId}`
            : "/my-questions",
        );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  function mergeSelected() {
    const selected = drafts.filter((d) => d.selected && !d.savedId);
    if (
      selected.length < 2 ||
      new Set(selected.map((d) => d.document.skill)).size !== 1
    ) {
      setError("Chọn ít nhất hai mục cùng kỹ năng để gộp.");
      return;
    }
    const skill = selected[0].document.skill;
    const content = {
      writing: selected.flatMap((d) => d.document.content.writing),
      speaking: selected.flatMap((d) => d.document.content.speaking),
      reading: selected.flatMap((d) => d.document.content.reading),
    };
    if (
      (skill === "writing" &&
        (content.writing.length !== 2 ||
          new Set(content.writing.map((q) => q.task_type)).size !== 2)) ||
      (skill === "speaking" &&
        (content.speaking.length !== 3 ||
          new Set(content.speaking.map((q) => q.part)).size !== 3)) ||
      (skill === "reading" &&
        (content.reading.length > 4 ||
          content.reading.reduce((n, p) => n + p.questions.length, 0) > 40))
    ) {
      setError(
        "Writing đầy đủ cần Task 1+2; Speaking cần Part 1+2+3; Reading tối đa 4 bài/40 câu.",
      );
      return;
    }
    content.writing.sort((a, b) => a.task_type - b.task_type);
    content.speaking.sort((a, b) => a.part - b.part);
    const document: LibraryDocument = {
      ...selected[0].document,
      title: `${skillLabels[skill]} · Đề đã gộp`,
      part:
        skill === "reading" &&
        (content.reading.length !== 4 ||
          content.reading.reduce((n, p) => n + p.questions.length, 0) !== 40)
          ? "mini"
          : "full",
      content,
      asset_ids: [...new Set(selected.flatMap((d) => d.document.asset_ids))],
    };
    setDrafts([
      {
        document,
        selected: true,
        confidence: selected[0].confidence,
        warnings: selected.flatMap((d) => d.warnings),
      },
      ...drafts.filter((d) => !d.selected || d.savedId),
    ]);
    setActive(0);
    setError("");
  }
  return (
    <div className="space-y-6">
      <header>
        <Link
          href={isAdmin ? "/admin/questions" : "/my-questions"}
          className="text-sm text-teal-800"
        >
          ← {isAdmin ? "Ngân hàng đề" : "Đề của tôi"}
        </Link>
        <h1 className="mt-3 text-3xl font-semibold">
          {isAdmin ? "Nhập và soạn đề" : "Thêm đề vào thư viện"}
        </h1>
        <p className="mt-2 text-stone-500">
          {isAdmin
            ? "Chọn nguồn, phân tích bằng AI nếu cần, rà soát nội dung rồi lưu bản soạn. Sau khi lưu, đưa đề vào ngân hàng từ trang chi tiết."
            : "Nhập đề bạn tìm được, kiểm tra nội dung rồi luyện bằng các công cụ quen thuộc."}
        </p>
      </header>
      {isAdmin && (
        <ol aria-label="Các bước nhập đề" className="grid gap-2 sm:grid-cols-4">
          {[
            ["1", "Nguồn nhập"],
            ["2", "AI phân tích"],
            ["3", "Rà soát"],
            ["4", "Lưu bản soạn"],
          ].map(([number, label], index) => {
            const current = !drafts.length ? (busy ? 1 : 0) : 2;
            return (
              <li
                key={number}
                aria-current={current === index ? "step" : undefined}
                className={
                  "rounded-lg border px-3 py-2.5 text-sm " +
                  (index === current
                    ? "border-teal-500 bg-teal-50 font-semibold text-teal-900"
                    : index < current
                      ? "border-teal-200 bg-white text-teal-800"
                      : "border-slate-200 bg-white text-slate-500")
                }
              >
                {number}. {label}
              </li>
            );
          })}
        </ol>
      )}
      {!drafts.length && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            {(
              [
                { key: "paste", label: "Dán văn bản", Icon: FileText },
                { key: "file", label: "Ảnh hoặc PDF", Icon: ImagePlus },
                { key: "manual", label: "Nhập thủ công", Icon: PenLine },
              ] as const
            ).map(({ key, label, Icon }) => (
              <button
                key={key}
                disabled={!!busy}
                onClick={() => {
                  setMethod(key);
                  setError("");
                }}
                className={`flex items-center gap-3 rounded-xl border p-5 text-left ${method === key ? "border-teal-700 bg-teal-50 text-teal-900" : "border-stone-200 bg-white"}`}
              >
                <Icon size={20} />
                {label}
              </button>
            ))}
          </div>
          <section className="panel space-y-4 p-6">
            {method === "paste" && (
              <Field
                label="Dán nguyên văn đề tại đây"
                value={raw}
                onChange={setRaw}
                multiline
                rows={14}
                hint="Có thể dán nhiều đề. Bao gồm các lựa chọn và đáp án nếu nguồn có sẵn."
              />
            )}
            {method === "file" && (
              <>
                <label className="block space-y-3">
                  <span className="font-medium">Chọn ảnh hoặc PDF</span>
                  <input
                    type="file"
                    accept=".jpg,.jpeg,.png,.webp,.pdf"
                    className="field block w-full"
                    onChange={(e) => {
                      setFile(e.target.files?.[0] || null);
                      setAssetId(null);
                      setError("");
                    }}
                  />
                </label>
                <p className="text-sm text-stone-500">
                  JPG, PNG, WEBP hoặc PDF · Tối đa 20 MB · PDF tối đa 20 trang ·
                  Ảnh tĩnh tối đa 25 megapixel.
                </p>
                {file && (
                  <p className="text-sm">
                    {file.name} · {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                )}
              </>
            )}
            {method === "manual" ? (
              <>
                <p className="text-sm text-stone-600">
                  Chọn kỹ năng, điền nội dung gốc và lưu. Reading không bắt buộc
                  có sẵn đáp án.
                </p>
                <Button
                  onClick={() => {
                    setDrafts([
                      {
                        document: emptyDocument(),
                        confidence: { skill: 1, part: 1, answer_key: null },
                        warnings: [],
                        selected: true,
                      },
                    ]);
                    setTab("edit");
                  }}
                >
                  Mở biểu mẫu
                </Button>
              </>
            ) : (
              <Button
                disabled={
                  !!busy ||
                  (method === "paste" ? raw.trim().length < 10 : !file)
                }
                onClick={analyze}
              >
                Phân tích đề
              </Button>
            )}
          </section>
        </>
      )}
      {warnings.map((w, i) => (
        <p
          key={i}
          role="status"
          className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900"
        >
          {w}
        </p>
      ))}
      {!!drafts.length && (
        <div className="grid items-start gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="panel space-y-3 p-4">
            <h2 className="font-semibold">{drafts.length} mục nhận diện</h2>
            {drafts.map((d, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 rounded-lg p-2 ${active === i ? "bg-teal-50" : "bg-stone-50"}`}
              >
                <input
                  aria-label={`Chọn mục ${i + 1}`}
                  type="checkbox"
                  className="mt-1"
                  checked={d.selected}
                  disabled={!!d.savedId || !!busy}
                  onChange={(e) =>
                    setDrafts((prev) =>
                      prev.map((v, n) =>
                        n === i ? { ...v, selected: e.target.checked } : v,
                      ),
                    )
                  }
                />
                <button
                  className="min-w-0 text-left text-sm"
                  onClick={() => {
                    setActive(i);
                    setTab("preview");
                  }}
                >
                  <span className="block font-medium">
                    {d.document.title || `Đề ${i + 1}`}
                  </span>
                  <span className="text-xs text-stone-500">
                    {skillLabels[d.document.skill]} ·{" "}
                    {partLabels[d.document.part]}
                    {d.savedId && " · Đã lưu"}
                  </span>
                </button>
              </div>
            ))}
            {drafts.length > 1 && (
              <Button
                size="sm"
                variant="outline"
                disabled={!!busy}
                onClick={mergeSelected}
              >
                Gộp các mục đã chọn
              </Button>
            )}
            <Button
              variant="ghost"
              disabled={!!busy}
              onClick={() => {
                setDrafts([]);
                setError("");
                setDuplicate(null);
              }}
            >
              Quay lại nguồn nhập
            </Button>
          </aside>
          <section className="panel space-y-5 p-5 sm:p-7">
            {drafts[active] && (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant={tab === "preview" ? "default" : "outline"}
                      onClick={() => setTab("preview")}
                    >
                      Xem trước
                    </Button>
                    <Button
                      size="sm"
                      variant={tab === "edit" ? "default" : "outline"}
                      onClick={() => setTab("edit")}
                    >
                      Chỉnh sửa
                    </Button>
                  </div>
                  <span className="text-xs text-stone-500">
                    Nhận diện kỹ năng{" "}
                    {Math.round(drafts[active].confidence.skill * 100)}% · Phần
                    thi {Math.round(drafts[active].confidence.part * 100)}%
                  </span>
                </div>
                {drafts[active].warnings.map((w, i) => (
                  <p
                    key={i}
                    className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900"
                  >
                    {w}
                  </p>
                ))}
                {Math.min(
                  drafts[active].confidence.skill,
                  drafts[active].confidence.part,
                ) < 0.8 && (
                  <p className="text-sm text-amber-900">
                    Một số nội dung có thể chưa được nhận diện đúng. Hãy đối
                    chiếu nguồn trước khi lưu.
                  </p>
                )}
                {tab === "preview" || drafts[active].savedId ? (
                  <DocumentPreview value={drafts[active].document} />
                ) : (
                  <DocumentForm
                    value={drafts[active].document}
                    onChange={update}
                    collections={collections}
                    onCollection={(c) => setCollections((prev) => [...prev, c])}
                  />
                )}
              </>
            )}
          </section>
        </div>
      )}
      {error && (
        <p
          className="rounded-lg bg-red-50 p-4 text-sm text-red-800"
          role="alert"
        >
          {error}
        </p>
      )}
      {duplicate && (
        <div className="flex flex-wrap items-center gap-4 rounded-lg border border-amber-300 p-4">
          <Link
            href={`/my-questions/detail?id=${duplicate.id}`}
            target="_blank"
            className="text-sm text-teal-800 underline"
          >
            Xem đề đã có: {duplicate.title}
          </Link>
          <Button
            variant="outline"
            disabled={!!busy}
            onClick={() => save(duplicate.index)}
          >
            Vẫn lưu thêm bản mới
          </Button>
        </div>
      )}
      {busy && (
        <p role="status" className="text-sm text-teal-800">
          {busy}
        </p>
      )}
      {!!drafts.length && (
        <div className="sticky bottom-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-stone-200 bg-white p-4 shadow-lg">
          <p className="text-sm text-stone-500">
            {isAdmin
              ? "Kiểm tra nội dung và đáp án trước khi lưu. Bản soạn chưa xuất bản vào ngân hàng."
              : "Đề chỉ được lưu khi bạn bấm nút. Hãy kiểm tra nội dung và đáp án trước khi lưu."}
          </p>
          <Button
            disabled={!!busy || !drafts.some((d) => d.selected && !d.savedId)}
            onClick={() => save()}
          >
            {isAdmin ? "Lưu bản soạn" : "Lưu"}{" "}
            {drafts.filter((d) => d.selected && !d.savedId).length} đề đã chọn
          </Button>
        </div>
      )}
    </div>
  );
}
