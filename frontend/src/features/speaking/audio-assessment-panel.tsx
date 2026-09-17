"use client";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  audioScoreLabels,
  coachLink,
  type AudioAssessment,
} from "./pronunciation-types";
import { scoreText } from "./types";

export function AudioAssessmentPanel({
  analysis,
  sourceAnswerId,
  practice = false,
}: {
  analysis: AudioAssessment;
  sourceAnswerId?: string;
  practice?: boolean;
}) {
  return (
    <section className="panel space-y-5 p-5 sm:p-7">
      <div>
        <h2 className="text-lg font-bold">Phát âm từ bản ghi của bạn</h2>
        <p className="mt-2 text-xs leading-6 text-stone-500">
          Điểm AI ước tính dựa trên âm thanh. Chỉ hiển thị vấn đề được nghe rõ
          với độ tin cậy đủ cao.
        </p>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {Object.entries(audioScoreLabels).map(([key, label]) => (
          <div key={key} className="rounded-xl bg-stone-50 p-3">
            <p className="text-xs text-stone-500">{label}</p>
            <p className="mt-2 text-xl font-bold text-teal-800">
              {scoreText(analysis[key as keyof typeof audioScoreLabels])}
              <span className="text-xs font-normal text-stone-400"> / 10</span>
            </p>
          </div>
        ))}
      </div>
      {analysis.reason_vi && (
        <p className="rounded-lg bg-amber-50 p-4 text-sm leading-6 text-amber-900">
          {analysis.reason_vi}
        </p>
      )}
      {analysis.pronunciation_summary_vi && (
        <p className="text-sm leading-7 text-stone-600">
          {analysis.pronunciation_summary_vi}
        </p>
      )}
      {analysis.fluency_summary_vi && (
        <p className="text-sm leading-7 text-stone-600">
          {analysis.fluency_summary_vi}
        </p>
      )}
      {practice && (
        <div className="space-y-3">
          {[
            ["Trọng âm", analysis.stress_feedback_vi],
            ["Điểm cần chú ý", analysis.issue_vi],
            ["Cách luyện tiếp", analysis.practice_tip_vi],
          ].map(
            ([label, text]) =>
              text && (
                <p key={label} className="text-sm leading-7">
                  <strong>{label}: </strong>
                  {text}
                </p>
              ),
          )}
        </div>
      )}
      {!!analysis.issues?.length && (
        <div className="space-y-4">
          <h3 className="font-semibold">Những từ/cụm từ cần chú ý</h3>
          {analysis.issues.map((issue, i) => (
            <article key={i} className="rounded-xl border border-stone-200 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <strong lang="en" className="text-teal-900">
                  {issue.target}
                </strong>
                <span className="text-xs text-stone-400">
                  Độ tin cậy {Math.round(issue.confidence * 100)}%
                </span>
              </div>
              <p className="mt-3 text-sm leading-7">{issue.description_vi}</p>
              <p className="mt-2 text-sm leading-7 text-stone-500">
                {issue.suggestion_vi}
              </p>
              <Button asChild className="mt-3" size="sm" variant="outline">
                <Link
                  href={coachLink(issue.target, sourceAnswerId, issue.type)}
                >
                  {issue.target.trim().includes(" ")
                    ? "Luyện câu này"
                    : "Luyện từ này"}
                </Link>
              </Button>
            </article>
          ))}
        </div>
      )}
      {analysis.available && !analysis.issues?.length && (
        <p className="text-sm text-stone-500">
          Chưa có lỗi cụ thể đủ chắc chắn để chỉ ra trong bản ghi này.
        </p>
      )}
    </section>
  );
}
