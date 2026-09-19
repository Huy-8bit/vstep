"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Field } from "./form-fields";
import type { Letter, ReadingItem } from "./types";
export function parseAnswerKey(
  raw: string,
  count: number,
): { values: Map<number, Letter>; error: string } {
  const regex = /(\d+)\s*[.:)=\-]?\s*([A-D])\b/gi;
  const values = new Map<number, Letter>();
  let error = "";
  for (const match of raw.matchAll(regex)) {
    const number = Number(match[1]);
    if (number < 1 || number > count || values.has(number))
      error =
        "Số câu bị lặp hoặc nằm ngoài đề. Kiểm tra lại trước khi áp dụng.";
    values.set(number, match[2].toUpperCase() as Letter);
  }
  if (raw.replace(regex, "").replace(/[\s,;]+/g, "") || !values.size)
    error = "Dùng dạng 1A 2C hoặc mỗi đáp án trên một dòng.";
  return { values, error };
}
export function AnswerKeyEditor({
  value,
  onChange,
}: {
  value: ReadingItem[];
  onChange: (items: ReadingItem[]) => void;
}) {
  const [raw, setRaw] = useState("");
  const [preview, setPreview] = useState(false);
  const [notice, setNotice] = useState("");
  const questions = value.flatMap((p) => p.questions);
  const parsed = parseAnswerKey(raw, questions.length);
  const known = questions.filter(
    (q) =>
      q.correct_answer &&
      ["provided", "user_confirmed"].includes(q.answer_key_source),
  ).length;
  return (
    <section className="space-y-3 rounded-xl border border-amber-200 bg-amber-50/60 p-5">
      <h3 className="font-semibold">
        Đặt đáp án · {known}/{questions.length} câu đã có đáp án
      </h3>
      {known < questions.length && (
        <p className="text-sm text-amber-900">
          Chưa có đủ đáp án. Bạn vẫn có thể luyện; hệ thống chưa thể tính điểm
          chính xác cho toàn bài.
        </p>
      )}
      <Field
        label="Nhập đáp án hàng loạt"
        value={raw}
        multiline
        rows={2}
        onChange={(v) => {
          setRaw(v);
          setPreview(false);
          setNotice("");
        }}
        hint="Ví dụ: 1A 2C 3B. Đánh số theo thứ tự câu trong toàn đề, từ 1; các câu không nhập giữ nguyên đáp án hiện tại."
      />
      <Button
        variant="outline"
        onClick={() => {
          setPreview(true);
          setNotice("");
        }}
      >
        Xem trước đáp án
      </Button>
      {preview &&
        (parsed.error ? (
          <p className="text-sm text-red-700" role="alert">
            {parsed.error}
          </p>
        ) : (
          <div className="space-y-3">
            <p className="flex flex-wrap gap-2">
              {[...parsed.values].map(([n, answer]) => (
                <span className="rounded bg-white px-2 py-1 text-sm" key={n}>
                  {n}. {answer}
                </span>
              ))}
            </p>
            <Button
              onClick={() => {
                let number = 0;
                onChange(
                  value.map((p) => ({
                    ...p,
                    questions: p.questions.map((q) => {
                      number++;
                      const answer = parsed.values.get(number);
                      return answer
                        ? {
                            ...q,
                            correct_answer: answer,
                            answer_key_source: "user_confirmed",
                            answer_key_evidence: null,
                          }
                        : q;
                    }),
                  })),
                );
                setPreview(false);
                setRaw("");
                setNotice(
                  "Đã áp dụng vào bản chỉnh sửa. Bấm Lưu đề để lưu phiên bản mới.",
                );
              }}
            >
              Xác nhận và áp dụng {parsed.values.size} đáp án
            </Button>
          </div>
        ))}
      {notice && (
        <p role="status" className="text-sm text-teal-800">
          {notice}
        </p>
      )}
    </section>
  );
}
