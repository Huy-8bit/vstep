import { Button } from "@/components/ui/button";
import { Field, Lines } from "./form-fields";
import type { SpeakingItem } from "./types";
export function SpeakingForm({
  value,
  onChange,
}: {
  value: SpeakingItem;
  onChange: (q: SpeakingItem) => void;
}) {
  const patch = (changes: Partial<SpeakingItem>) =>
    onChange({ ...value, ...changes });
  return (
    <section className="space-y-5 rounded-xl border border-stone-200 p-5">
      <h3 className="font-semibold">Speaking Part {value.part}</h3>
      <Field
        label="Chủ đề gốc"
        value={value.topic}
        onChange={(topic) => patch({ topic })}
      />
      {value.part === 1 && (
        <>
          {value.topic_sets.map((topic, i) => (
            <div key={i} className="space-y-3 rounded-lg bg-stone-50 p-4">
              <Field
                label={`Chủ đề ${i + 1}`}
                value={topic.topic}
                onChange={(v) =>
                  patch({
                    topic_sets: value.topic_sets.map((t, n) =>
                      n === i ? { ...t, topic: v } : t,
                    ),
                  })
                }
              />
              <Lines
                label="Câu hỏi"
                values={topic.questions}
                onChange={(questions) =>
                  patch({
                    topic_sets: value.topic_sets.map((t, n) =>
                      n === i ? { ...t, questions } : t,
                    ),
                  })
                }
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() =>
                  patch({
                    topic_sets: value.topic_sets.filter((_, n) => n !== i),
                  })
                }
              >
                Bỏ chủ đề này
              </Button>
            </div>
          ))}
          <Button
            variant="outline"
            disabled={value.topic_sets.length >= 6}
            onClick={() =>
              patch({
                topic_sets: [...value.topic_sets, { topic: "", questions: [] }],
              })
            }
          >
            Thêm chủ đề
          </Button>
        </>
      )}
      {value.part === 2 && (
        <>
          <Field
            label="Tình huống / Situation"
            value={value.situation}
            multiline
            onChange={(situation) => patch({ situation })}
          />
          {[0, 1, 2].map((i) => (
            <Field
              key={i}
              label={`Lựa chọn ${i + 1}`}
              value={value.options[i] || ""}
              multiline
              rows={2}
              onChange={(v) =>
                patch({
                  options: Array.from({ length: 3 }, (_, n) =>
                    n === i ? v : value.options[n] || "",
                  ),
                })
              }
            />
          ))}
          <Field
            label="Yêu cầu cho thí sinh / Candidate task"
            value={value.candidate_task}
            multiline
            onChange={(candidate_task) => patch({ candidate_task })}
          />
          <Field
            label="Ngữ cảnh bổ sung (nếu có)"
            value={value.optional_context}
            multiline
            onChange={(optional_context) => patch({ optional_context })}
          />
        </>
      )}
      {value.part === 3 && (
        <>
          <Field
            label="Ý chính / Central idea"
            value={value.central_idea}
            multiline
            onChange={(central_idea) => patch({ central_idea })}
          />
          <Lines
            label="Ý gợi ý trong đề"
            values={value.suggested_ideas}
            onChange={(suggested_ideas) => patch({ suggested_ideas })}
          />
          <Lines
            label="Câu hỏi mở rộng"
            values={value.follow_up_questions}
            onChange={(follow_up_questions) => patch({ follow_up_questions })}
          />
        </>
      )}
    </section>
  );
}
