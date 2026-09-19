import { Button } from "@/components/ui/button";
import { questionTypes } from "@/features/reading/types";
import { AnswerKeyEditor } from "./answer-key-editor";
import { Field, SelectField } from "./form-fields";
import {
  emptyReading,
  emptyReadingQuestion,
  keyLabels,
  type Letter,
  type ReadingItem,
} from "./types";
export function ReadingForm({
  value,
  onChange,
}: {
  value: ReadingItem[];
  onChange: (q: ReadingItem[]) => void;
}) {
  const total = value.reduce((n, p) => n + p.questions.length, 0);
  const patch = (index: number, changes: Partial<ReadingItem>) =>
    onChange(value.map((p, i) => (i === index ? { ...p, ...changes } : p)));
  return (
    <div className="space-y-5">
      <AnswerKeyEditor value={value} onChange={onChange} />
      {value.map((passage, index) => (
        <section
          key={index}
          className="space-y-5 rounded-xl border border-stone-200 p-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="font-semibold">
              Bài đọc {index + 1} · {passage.questions.length} câu
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onChange(value.filter((_, i) => i !== index))}
            >
              Bỏ bài đọc
            </Button>
          </div>
          <Field
            label="Tiêu đề bài đọc"
            value={passage.title}
            onChange={(title) => patch(index, { title })}
          />
          <Field
            label="Nội dung bài đọc"
            value={passage.passage_text}
            multiline
            rows={12}
            onChange={(passage_text) => patch(index, { passage_text })}
            hint="Giữ nguyên bài đọc, ngắt đoạn bằng dòng trống."
          />
          {passage.questions.map((question, qi) => {
            const update = (changes: Partial<typeof question>) =>
              patch(index, {
                questions: passage.questions.map((q, i) =>
                  i === qi ? { ...q, ...changes } : q,
                ),
              });
            const displayNumber =
              value
                .slice(0, index)
                .reduce((n, p) => n + p.questions.length, 0) +
              qi +
              1;
            return (
              <details
                key={qi}
                className="rounded-lg border border-stone-200 bg-stone-50 p-4"
                open={!question.question_text}
              >
                <summary className="cursor-pointer font-medium">
                  Câu {displayNumber} ·{" "}
                  {question.question_text.slice(0, 80) || "Nhập nội dung"}{" "}
                  <span className="text-xs font-normal text-stone-500">
                    · {keyLabels[question.answer_key_source]}
                  </span>
                </summary>
                <div className="mt-4 space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Field
                      label="Số câu trong nguồn gốc"
                      type="number"
                      value={String(question.question_number)}
                      onChange={(v) => update({ question_number: Number(v) })}
                    />
                    <SelectField
                      label="Dạng câu"
                      value={question.question_type}
                      onChange={(question_type) => update({ question_type })}
                    >
                      {Object.entries({
                        ...questionTypes,
                        multiple_choice: "Multiple choice",
                        vocabulary_in_context: "Vocabulary in context",
                        NOT_TRUE: "NOT TRUE",
                        other: "Khác / chưa xác định",
                      }).map(([key, label]) => (
                        <option key={key} value={key}>
                          {label}
                        </option>
                      ))}
                    </SelectField>
                  </div>
                  <Field
                    label="Nội dung câu hỏi"
                    value={question.question_text}
                    multiline
                    onChange={(question_text) => update({ question_text })}
                  />
                  {(["A", "B", "C", "D"] as Letter[]).map((letter) => (
                    <Field
                      key={letter}
                      label={`Lựa chọn ${letter}`}
                      value={question.options[letter]}
                      multiline
                      rows={2}
                      onChange={(v) =>
                        update({
                          options: { ...question.options, [letter]: v },
                        })
                      }
                    />
                  ))}
                  <SelectField
                    label="Đáp án đúng (bạn xác nhận)"
                    value={question.correct_answer || ""}
                    onChange={(v) =>
                      update({
                        correct_answer: (v || null) as Letter | null,
                        answer_key_source: v ? "user_confirmed" : "unknown",
                        answer_key_evidence: null,
                      })
                    }
                  >
                    <option value="">Chưa có đáp án</option>
                    {["A", "B", "C", "D"].map((v) => (
                      <option key={v}>{v}</option>
                    ))}
                  </SelectField>
                  <Field
                    label="Giải thích từ nguồn / ghi chú của bạn (nếu có)"
                    value={question.explanation || ""}
                    multiline
                    onChange={(explanation) =>
                      update({ explanation: explanation || null })
                    }
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      patch(index, {
                        questions: passage.questions.filter((_, i) => i !== qi),
                      })
                    }
                  >
                    Bỏ câu này
                  </Button>
                </div>
              </details>
            );
          })}
          <Button
            variant="outline"
            disabled={total >= 40}
            onClick={() =>
              patch(index, {
                questions: [
                  ...passage.questions,
                  emptyReadingQuestion(
                    Math.max(
                      0,
                      ...passage.questions.map((q) => q.question_number),
                    ) + 1,
                  ),
                ],
              })
            }
          >
            Thêm câu hỏi
          </Button>
        </section>
      ))}
      <Button
        variant="outline"
        disabled={value.length >= 4 || total >= 40}
        onClick={() => onChange([...value, emptyReading()])}
      >
        Thêm bài đọc
      </Button>
      <p className="text-xs text-stone-500">
        Tổng {total} câu · Một đề có tối đa 4 bài đọc, 40 câu. Mini practice
        không cần đủ 40 câu.
      </p>
    </div>
  );
}
