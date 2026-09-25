import { apiUrl } from "@/services/api";
import {
  partLabels,
  skillLabels,
  keyLabels,
  type LibraryDocument,
  type Letter,
} from "./types";
function Text({ children }: { children: string }) {
  return (
    <p className="whitespace-pre-wrap leading-7">
      {children || "[Chưa có nội dung]"}
    </p>
  );
}
export function DocumentPreview({ value }: { value: LibraryDocument }) {
  return (
    <article className="space-y-6">
      <header>
        <p className="eyebrow">
          {skillLabels[value.skill]} · {partLabels[value.part]}
        </p>
        <h2 className="mt-2 text-2xl font-semibold">
          {value.title || "Đề chưa đặt tên"}
        </h2>
      </header>
      {value.content.writing.map((q) => (
        <section
          key={q.task_type}
          className="space-y-4 border-t border-stone-200 pt-5"
        >
          <h3 className="font-semibold">Task {q.task_type}</h3>
          <Text>{q.instruction}</Text>
          {q.stimulus_text && (
            <blockquote className="rounded-lg border-l-4 border-teal-600 bg-teal-50 p-5">
              <Text>{q.stimulus_text}</Text>
            </blockquote>
          )}
          {q.requirements.length > 0 && (
            <ul className="list-disc space-y-2 pl-5">
              {q.requirements.map((v, i) => (
                <li key={i} className="whitespace-pre-wrap">
                  {v}
                </li>
              ))}
            </ul>
          )}
          <p className="text-sm text-stone-500">
            Tối thiểu {q.minimum_words || (q.task_type === 1 ? 120 : 250)} từ
            {q.minimum_words === null && " (mặc định luyện tập)"}.
          </p>
        </section>
      ))}
      {value.content.speaking.map((q) => (
        <section
          key={q.part}
          className="space-y-4 border-t border-stone-200 pt-5"
        >
          <h3 className="font-semibold">
            Part {q.part}
            {q.topic && ` · ${q.topic}`}
          </h3>
          {q.part === 1 &&
            q.topic_sets.map((t, i) => (
              <div key={i}>
                <h4 className="font-medium">{t.topic}</h4>
                <ol className="mt-2 list-decimal space-y-2 pl-5">
                  {t.questions.map((v, n) => (
                    <li key={n}>{v}</li>
                  ))}
                </ol>
              </div>
            ))}
          {q.part === 2 && (
            <>
              <Text>{q.situation}</Text>
              {q.optional_context && <Text>{q.optional_context}</Text>}
              <ol className="list-decimal space-y-2 pl-5">
                {q.options.map((v, n) => (
                  <li key={n}>{v || "[Thiếu lựa chọn]"}</li>
                ))}
              </ol>
              <Text>{q.candidate_task}</Text>
            </>
          )}
          {q.part === 3 && (
            <>
              <div className="rounded-xl bg-teal-50 p-5 text-center font-medium">
                <Text>{q.central_idea}</Text>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                {q.suggested_ideas.map((v, n) => (
                  <div
                    className="rounded-lg border border-teal-200 p-4"
                    key={n}
                  >
                    {v}
                  </div>
                ))}
              </div>
              <p className="text-sm text-stone-500">
                Bạn có thể bổ sung ý của mình.
              </p>
              <ol className="list-decimal space-y-2 pl-5">
                {q.follow_up_questions.map((v, n) => (
                  <li key={n}>{v}</li>
                ))}
              </ol>
            </>
          )}
        </section>
      ))}
      {value.content.reading.map((p, i) => (
        <section key={i} className="space-y-4 border-t border-stone-200 pt-5">
          <h3 className="font-semibold">
            Bài đọc {i + 1} · {p.title}
          </h3>
          <Text>{p.passage_text}</Text>
          {p.questions.map((q, n) => (
            <div key={n} className="space-y-2 rounded-lg bg-stone-50 p-4">
              <p className="font-medium">
                {q.question_number}. {q.question_text}
              </p>
              {(["A", "B", "C", "D"] as Letter[]).map((letter) => (
                <p key={letter}>
                  {letter}. {q.options[letter] || "[Thiếu lựa chọn]"}
                </p>
              ))}
              <p className="text-sm text-teal-800">
                {keyLabels[q.answer_key_source]}
                {q.correct_answer && `: ${q.correct_answer}`}
              </p>
              {q.explanation && <Text>{q.explanation}</Text>}
            </div>
          ))}
        </section>
      ))}
      {value.asset_ids.length > 0 && (
        <aside className="space-y-2 rounded-xl border border-stone-200 p-4">
          <h3 className="font-medium">
            Tệp nguồn được lưu riêng trong thư viện
          </h3>
          <p className="text-xs text-stone-500">
            Đối chiếu ảnh, sơ đồ và bố cục gốc tại đây trước khi luyện.
          </p>
          {value.asset_ids.map((id, i) => (
            <a
              className="block text-sm text-teal-800 underline"
              href={apiUrl(`/my-questions/assets/${id}`)}
              key={id}
              target="_blank"
              rel="noreferrer"
            >
              Mở tệp nguồn {i + 1}
            </a>
          ))}
        </aside>
      )}
    </article>
  );
}
