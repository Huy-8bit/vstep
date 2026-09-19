import { Field, Lines, SelectField } from "./form-fields";
import type { WritingItem } from "./types";
export function WritingForm({
  value,
  onChange,
}: {
  value: WritingItem;
  onChange: (q: WritingItem) => void;
}) {
  const patch = (changes: Partial<WritingItem>) =>
    onChange({ ...value, ...changes });
  return (
    <section className="space-y-5 rounded-xl border border-stone-200 p-5">
      <h3 className="font-semibold">Writing Task {value.task_type}</h3>
      <Field
        label={
          value.task_type === 1
            ? "Yêu cầu đề bài / Instruction"
            : "Đề bài / Prompt"
        }
        value={value.instruction}
        multiline
        rows={5}
        onChange={(instruction) => patch({ instruction })}
      />
      <div className="grid gap-4 sm:grid-cols-2">
        {value.task_type === 1 ? (
          <SelectField
            label="Dạng nội dung nguồn"
            value={value.stimulus_type}
            onChange={(stimulus_type) => patch({ stimulus_type })}
          >
            {[
              "letter",
              "email",
              "announcement",
              "situation",
              "request",
              "invitation",
              "complaint",
              "other",
            ].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </SelectField>
        ) : (
          <SelectField
            label="Dạng bài luận"
            value={value.essay_family}
            onChange={(essay_family) => patch({ essay_family })}
          >
            {[
              "opinion",
              "discussion",
              "problem-solution",
              "causes-solutions",
              "advantages-disadvantages",
              "issue-response",
              "other",
            ].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </SelectField>
        )}
        <Field
          label="Số từ tối thiểu"
          type="number"
          value={value.minimum_words?.toString() ?? ""}
          hint={`Để trống: dùng mặc định ${value.task_type === 1 ? 120 : 250} từ.`}
          onChange={(v) => patch({ minimum_words: v ? Number(v) : null })}
        />
      </div>
      <Field
        label="Nội dung thư / email / tình huống gốc (nếu có)"
        value={value.stimulus_text}
        multiline
        rows={7}
        onChange={(stimulus_text) => patch({ stimulus_text })}
      />
      <Lines
        label="Các yêu cầu riêng trong đề (nếu có)"
        values={value.requirements}
        onChange={(requirements) => patch({ requirements })}
      />
    </section>
  );
}
