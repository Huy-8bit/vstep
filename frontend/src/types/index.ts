import type { WritingAssessmentMetadata } from "@/features/grading/writing-evidence";
import type { TestProfile } from "@/lib/test-profile";
export type Mode = "FULL_TEST" | "TASK1" | "TASK2";
export type User = { id: string; email: string };
export type Question = {
  id: string;
  task_type: 1 | 2;
  question_type: string;
  topic: string;
  test_profile: TestProfile;
  instruction: string;
  requirements: string[];
  stimulus: string | null;
  response_instruction: string | null;
  genre: string | null;
  register: string | null;
  recipient_relationship: string | null;
  purpose: string | null;
  minimum_words: number;
  source: "SEED" | "AI";
};
export type Improvement = {
  title_vi: string;
  explanation_vi: string;
  example: string;
};
export type WritingError = {
  id: string;
  category: string;
  subtype: string;
  original: string;
  corrected: string;
  explanation_vi: string;
  severity: string;
};
export type Grading = WritingAssessmentMetadata & {
  id: string;
  scores: {
    task_fulfillment: number;
    organization: number;
    vocabulary: number;
    grammar: number;
    overall: number;
  };
  summary_vi: string;
  strengths: string[];
  priority_improvements: Improvement[];
  structure_feedback: Improvement[];
  task_fulfillment_feedback: Improvement[];
  errors: WritingError[];
  vocabulary_suggestions: {
    original: string;
    suggestion: string;
    reason_vi: string;
    example: string;
  }[];
  sentence_feedback: {
    original: string;
    corrected: string;
    explanation_vi: string;
  }[];
  corrected_version: string;
  improved_b2_version: string;
  ai_model: string;
  prompt_version: string;
  current_grader_version: string;
};
export type Attempt = {
  id: string;
  exam_session_id: string;
  task_type: 1 | 2;
  answer: string;
  word_count: number;
  revision: number;
  started_at: string;
  submitted_at: string | null;
  duration_seconds: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  question: Question;
  grading: Grading | null;
  mode?: Mode;
};
export type Exam = {
  id: string;
  mode: Mode;
  started_at: string;
  expires_at: string | null;
  submitted_at: string | null;
  status: string;
  server_now: string;
  overall_score: number | null;
  writing_reference_level: string | null;
  attempts: Attempt[];
};
export type AttemptDetail = Attempt & { exam: Exam };
export type Progress = {
  graded_attempts: number;
  completed_full_tests: number;
  average_writing_score: number | null;
  average_task_score: number | null;
  criteria: Record<string, number | null>;
  total_words: number;
  progression: {
    date: string;
    score: number;
    mode: Mode;
    attempt_id: string;
  }[];
};
export type ErrorStat = { category: string; subtype: string; count: number };
