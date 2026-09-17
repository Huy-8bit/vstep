export const audioScoreLabels = {
  pronunciation_score: "Phát âm",
  intelligibility_score: "Mức độ dễ hiểu",
  clarity_score: "Độ rõ",
  stress_score: "Trọng âm",
  intonation_score: "Ngữ điệu",
  rhythm_score: "Nhịp điệu",
  fluency_score: "Độ trôi chảy",
};
export type AudioIssue = {
  type: string;
  target: string;
  description_vi: string;
  suggestion_vi: string;
  confidence: number;
  audible_evidence_vi?: string;
};
export type AudioAssessment = Partial<
  Record<keyof typeof audioScoreLabels, number | null>
> & {
  available: boolean;
  reason_vi: string | null;
  confidence?: number;
  pronunciation_summary_vi?: string;
  fluency_summary_vi?: string;
  issues?: AudioIssue[];
  heard_text?: string;
  stress_feedback_vi?: string;
  issue_vi?: string;
  practice_tip_vi?: string;
};
export type PronunciationPractice = {
  id: string;
  reference_text: string;
  reference_hash: string;
  source_answer_id: string | null;
  source_issue_type: string | null;
  status: string;
  audio_url: string | null;
  audio_duration_ms: number | null;
  pronunciation_score: number | null;
  fluency_score: number | null;
  analysis: AudioAssessment | null;
  created_at: string;
  updated_at: string;
};
export type WordProgress = {
  reference_text: string;
  reference_hash: string;
  first_score: number;
  latest_score: number;
  attempts: number;
};
export type PronunciationProgressData = {
  attempts: number;
  scored_attempts: number;
  average_pronunciation: number | null;
  timeline: {
    id: string;
    date: string;
    reference_text: string;
    pronunciation: number | null;
    fluency: number | null;
  }[];
  recurring_issues: { type: string; target: string; count: number }[];
  difficult_words: WordProgress[];
  improved_words: WordProgress[];
};
export function coachLink(
  reference: string,
  sourceAnswerId?: string,
  issueType?: string,
) {
  const params = new URLSearchParams({ reference });
  if (sourceAnswerId) params.set("source", sourceAnswerId);
  if (issueType) params.set("issue", issueType);
  return `/speaking/pronunciation?${params}`;
}
