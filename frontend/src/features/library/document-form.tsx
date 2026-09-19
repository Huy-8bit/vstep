"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { post } from "@/services/api";
import { Field, SelectField } from "./form-fields";
import { WritingForm } from "./writing-form";
import { SpeakingForm } from "./speaking-form";
import { ReadingForm } from "./reading-form";
import {
  configure,
  partLabels,
  parts,
  skillLabels,
  type Collection,
  type LibraryDocument,
  type LibraryPart,
  type Skill,
} from "./types";
export function DocumentForm({
  value,
  onChange,
  collections,
  onCollection,
}: {
  value: LibraryDocument;
  onChange: (doc: LibraryDocument) => void;
  collections: Collection[];
  onCollection: (collection: Collection) => void;
}) {
  const patch = (changes: Partial<LibraryDocument>) =>
    onChange({ ...value, ...changes });
  const [collectionName, setCollectionName] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  return (
    <div className="space-y-6">
      {value.asset_ids.length > 0 && (
        <section className="rounded-xl bg-stone-50 p-4 text-sm">
          <p className="font-medium">Tệp cần hiển thị khi luyện</p>
          <p className="my-2 text-xs text-stone-500">
            Chọn ảnh hoặc tài liệu có sơ đồ/hình cần dùng trong bài. Chỉ chọn
            tệp chứa đề; tệp có đáp án nên để trong thư viện để xem sau.
          </p>
          {value.asset_ids.map((id, i) => (
            <label key={id} className="my-2 flex items-center gap-2">
              <input
                type="checkbox"
                checked={
                  value.content.practice_asset_ids?.includes(id) || false
                }
                onChange={(e) =>
                  patch({
                    content: {
                      ...value.content,
                      practice_asset_ids: e.target.checked
                        ? [...(value.content.practice_asset_ids || []), id]
                        : (value.content.practice_asset_ids || []).filter(
                            (v) => v !== id,
                          ),
                    },
                  })
                }
              />
              Hiển thị tệp nguồn {i + 1}{" "}
              <a
                href={`/api/v1/my-questions/assets/${id}`}
                target="_blank"
                rel="noreferrer"
                className="text-teal-800 underline"
              >
                Xem tệp
              </a>
            </label>
          ))}
        </section>
      )}
      <div className="grid gap-5 sm:grid-cols-2">
        <SelectField
          label="Kỹ năng"
          value={value.skill}
          onChange={(skill) =>
            onChange(configure(value, skill as Skill, parts[skill as Skill][0]))
          }
        >
          {Object.entries(skillLabels).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Phần thi"
          value={value.part}
          onChange={(part) =>
            onChange(configure(value, value.skill, part as LibraryPart))
          }
        >
          {parts[value.skill].map((part) => (
            <option key={part} value={part}>
              {partLabels[part]}
            </option>
          ))}
        </SelectField>
      </div>
      <Field
        label="Tên đề"
        value={value.title}
        onChange={(title) => patch({ title })}
      />
      {value.skill === "writing" &&
        value.content.writing.map((q, i) => (
          <WritingForm
            key={q.task_type}
            value={q}
            onChange={(question) =>
              patch({
                content: {
                  ...value.content,
                  writing: value.content.writing.map((v, n) =>
                    n === i ? question : v,
                  ),
                },
              })
            }
          />
        ))}
      {value.skill === "speaking" &&
        value.content.speaking.map((q, i) => (
          <SpeakingForm
            key={q.part}
            value={q}
            onChange={(question) =>
              patch({
                content: {
                  ...value.content,
                  speaking: value.content.speaking.map((v, n) =>
                    n === i ? question : v,
                  ),
                },
              })
            }
          />
        ))}
      {value.skill === "reading" && (
        <ReadingForm
          value={value.content.reading}
          onChange={(reading) =>
            patch({ content: { ...value.content, reading } })
          }
        />
      )}
      <details className="panel p-5" open>
        <summary className="cursor-pointer font-semibold">
          Phân loại và nguồn đề
        </summary>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <Field
            label="Chủ đề"
            value={value.topic}
            onChange={(topic) => patch({ topic })}
          />
          <Field
            label="Tag"
            value={value.tags.join(",")}
            onChange={(v) => patch({ tags: v.split(",") })}
            hint="Ngăn cách bằng dấu phẩy."
          />
          <SelectField
            label="Bộ sưu tập"
            value={value.collection_id || ""}
            onChange={(collection_id) =>
              patch({ collection_id: collection_id || null })
            }
          >
            <option value="">Chưa phân vào bộ sưu tập</option>
            {collections.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </SelectField>
          <SelectField
            label="Nguồn đề"
            value={value.source_type}
            onChange={(source_type) => patch({ source_type })}
          >
            {Object.entries({
              manual: "Tự nhập",
              copied_text: "Văn bản đã sao chép",
              image: "Ảnh",
              pdf: "PDF",
              teacher: "Giáo viên",
              website: "Website",
              book: "Sách",
              other: "Khác",
            }).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </SelectField>
          <Field
            label="Tên nguồn (tùy chọn)"
            value={value.source_name || ""}
            onChange={(source_name) => patch({ source_name })}
          />
          <Field
            label="URL nguồn (tùy chọn)"
            value={value.source_url || ""}
            onChange={(source_url) => patch({ source_url })}
            hint="Chỉ lưu để tham khảo; không tự lấy nội dung từ URL."
          />
        </div>
        <div className="mt-4 space-y-4">
          <Field
            label="Ghi chú riêng"
            value={value.notes || ""}
            multiline
            onChange={(notes) => patch({ notes })}
          />
          <div className="flex flex-wrap items-end gap-3">
            <Field
              label="Tạo bộ sưu tập mới"
              value={collectionName}
              onChange={setCollectionName}
            />
            <Button
              variant="outline"
              disabled={!collectionName.trim() || creating}
              onClick={async () => {
                setCreating(true);
                setError("");
                try {
                  const c = await post<Collection>(
                    "/my-questions/collections",
                    { name: collectionName },
                  );
                  onCollection(c);
                  patch({ collection_id: c.id });
                  setCollectionName("");
                } catch (e) {
                  setError((e as Error).message);
                } finally {
                  setCreating(false);
                }
              }}
            >
              Tạo bộ sưu tập
            </Button>
          </div>
          {error && (
            <p className="text-sm text-red-700" role="alert">
              {error}
            </p>
          )}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={value.favorite}
              onChange={(e) => patch({ favorite: e.target.checked })}
            />
            Đánh dấu yêu thích
          </label>
        </div>
      </details>
    </div>
  );
}
