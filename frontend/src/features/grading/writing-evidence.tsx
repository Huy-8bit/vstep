"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { api } from "@/services/api";
import { criteria } from "@/lib/constants";
import { score } from "@/lib/utils";
import type { Grading } from "@/types";

export type CriterionEvidence = {
  score: number;
  initial_score: number;
  assessment_vi: string;
  score_justification_vi: string;
  consistency_review_vi: string;
  high_score_justification_vi: string;
  positive_evidence: { quote: string; explanation_vi: string }[];
  negative_evidence: { quote: string; explanation_vi: string }[];
};
export type WritingAssessmentMetadata = {
  grader_version?: string;
  analysis_prompt_version?: string;
  calibration_prompt_version?: string;
  criterion_evidence?: Record<string, CriterionEvidence | string>;
  analysis_snapshot?: {
    metrics?: {
      word_count: number;
      sentence_count: number;
      number_of_detected_errors: number;
      major_error_count: number;
      minor_error_count: number;
      estimated_error_density: number;
      structures: Record<string, number>;
      relative_clauses: number;
      conditionals: number;
      subordination: number;
      note_vi: string;
    };
  };
  created_at?: string;
};
export function WritingEvidencePanel({ grading }: { grading: Grading }) {
  const metrics = grading.analysis_snapshot?.metrics;
  if (!metrics) return null;
  return (
    <details className="panel p-5 sm:p-7">
      <summary className="cursor-pointer font-semibold">
        Vì sao bạn nhận mức điểm này?
      </summary>
      <p className="mt-4 text-sm leading-7 text-stone-500">
        Điểm được chốt từ bài gốc trước khi tạo bản sửa và bài tham khảo. Đạt số
        từ hoặc trả lời đủ ý chưa đồng nghĩa với mức điểm cao.
      </p>
      <div className="my-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {[
          ["Số từ", metrics.word_count],
          ["Đơn vị câu", metrics.sentence_count],
          ["Lỗi đã nhận diện", metrics.number_of_detected_errors],
          ["Lỗi đáng kể", metrics.major_error_count],
          ["Lỗi nhẹ", metrics.minor_error_count],
          ["Lỗi / 100 từ", metrics.estimated_error_density],
        ].map(([label, value]) => (
          <div className="rounded-lg bg-stone-50 p-3" key={label}>
            <p className="text-xs text-stone-500">{label}</p>
            <p className="mt-2 font-bold">{value}</p>
          </div>
        ))}
      </div>
      <p className="text-xs leading-6 text-stone-500">{metrics.note_vi}</p>
      <p className="mt-3 text-sm leading-7 text-stone-600">
        Câu đơn: {metrics.structures.simple || 0} · Câu ghép:{" "}
        {metrics.structures.compound || 0} · Câu phức:{" "}
        {metrics.structures.complex || 0} · Ghép–phức:{" "}
        {metrics.structures.compound_complex || 0} · Mệnh đề quan hệ:{" "}
        {metrics.relative_clauses} · Điều kiện: {metrics.conditionals} · Mệnh đề
        phụ: {metrics.subordination}
      </p>
      <div className="mt-6 space-y-5">
        {Object.entries(criteria).map(([key, label]) => {
          const evidence = grading.criterion_evidence?.[key];
          if (!evidence || typeof evidence === "string") return null;
          return (
            <section
              key={key}
              className="rounded-xl border border-stone-200 p-5"
            >
              <h3 className="font-semibold">
                {label} · {score(evidence.score)} / 10
              </h3>
              <p className="mt-3 text-sm leading-7">
                {evidence.score_justification_vi}
              </p>
              {[
                {
                  title: "Bằng chứng làm tốt",
                  items: evidence.positive_evidence,
                },
                {
                  title: "Bằng chứng cần cải thiện",
                  items: evidence.negative_evidence,
                },
              ].map((group) => (
                <div key={group.title} className="mt-4">
                  <h4 className="text-xs font-semibold text-stone-500">
                    {group.title}
                  </h4>
                  {group.items.length ? (
                    group.items.map((item, i) => (
                      <div
                        key={i}
                        className="mt-3 border-l-2 border-teal-200 pl-3"
                      >
                        {item.quote && (
                          <blockquote
                            lang="en"
                            className="text-sm italic text-teal-900"
                          >
                            “{item.quote}”
                          </blockquote>
                        )}
                        <p className="mt-1 text-sm leading-7 text-stone-500">
                          {item.explanation_vi}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="mt-2 text-xs text-stone-400">
                      Không có trích dẫn bổ sung.
                    </p>
                  )}
                </div>
              ))}
              <p className="mt-4 rounded-lg bg-stone-50 p-3 text-xs leading-6 text-stone-600">
                Đối chiếu điểm với bằng chứng: {evidence.consistency_review_vi}
              </p>
            </section>
          );
        })}
      </div>
    </details>
  );
}
export function WritingGradingHistory({ attemptId }: { attemptId: string }) {
  const [previous, setPrevious] = useState<
    { id: string; grading: Grading }[] | null
  >(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    setBusy(true);
    setError("");
    try {
      const data = await api<{ previous: { id: string; grading: Grading }[] }>(
        `/attempts/${attemptId}/grading-history`,
      );
      setPrevious(data.previous);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <details
      className="panel p-5"
      onToggle={(e) => {
        if (e.currentTarget.open && previous === null && !busy) void load();
      }}
    >
      <summary className="cursor-pointer text-sm font-semibold">
        Lịch sử các phiên bản chấm
      </summary>
      {error && (
        <>
          <ErrorNotice message={error} />
          <Button size="sm" onClick={load}>
            Thử lại
          </Button>
        </>
      )}
      {busy && <p className="mt-4 text-sm">Đang tải...</p>}
      {previous && !previous.length && (
        <p className="mt-4 text-sm text-stone-500">
          Chưa có kết quả chấm cũ được thay thế.
        </p>
      )}
      {previous?.map((item) => (
        <details
          key={item.id}
          className="mt-4 rounded-xl border border-stone-200 p-4"
        >
          <summary className="cursor-pointer text-sm">
            Bộ chấm {item.grading.grader_version || "1.0.0"} ·{" "}
            {score(item.grading.scores.overall)} / 10 ·{" "}
            {item.grading.created_at
              ? new Date(item.grading.created_at).toLocaleString("vi-VN")
              : "Kết quả trước"}
          </summary>
          <p className="mt-3 text-sm leading-7">{item.grading.summary_vi}</p>
          <div className="mt-3 grid grid-cols-2 gap-3">
            {Object.entries(criteria).map(([key, label]) => (
              <p key={key} className="text-sm text-stone-600">
                {label}:{" "}
                {score(
                  item.grading.scores[key as keyof typeof item.grading.scores],
                )}
              </p>
            ))}
          </div>
          <WritingEvidencePanel grading={item.grading} />
          <p className="mt-4 text-xs text-stone-500">
            {item.grading.ai_model} · Prompt {item.grading.prompt_version}
          </p>
        </details>
      ))}
    </details>
  );
}
