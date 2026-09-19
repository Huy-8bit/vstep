export type Skill = "WRITING" | "SPEAKING" | "READING" | "CROSS";
export type Weakness = {
  id: string;
  skill: Skill;
  category: string;
  subcategory: string;
  concept_key: string;
  display_name_vi: string;
  display_name_en: string;
  occurrence_count: number;
  affected_attempt_count: number;
  recent_occurrence_count: number;
  status: string;
  mastery_status: string;
  trend: string;
  priority_score: number;
  first_seen_at: string;
  last_seen_at: string;
  stats: {
    skills: string[];
    by_skill: Record<string, number>;
    confidence_label: string;
    accuracy: number | null;
    question_count: number | null;
    exercise_accuracy: number | null;
    exercise_count: number;
    reuse_attempts: number;
    older_rate: number | null;
    recent_rate: number | null;
    unit: string;
    window_attempts: number;
  };
};
export type Lesson = {
  id: string;
  created_at: string;
  content: {
    title: string;
    why_this_matters_vi: string;
    simple_explanation_vi: string;
    rules: string[];
    examples: { english: string; explanation_vi: string }[];
    examples_from_user_errors: {
      signal_id: string;
      original: string;
      corrected: string | null;
      explanation_vi: string;
    }[];
    common_traps: string[];
    quick_check: string[];
    practice_recommendation: string;
    sources: { signal_id: string; source_url: string; skill: string }[];
  };
};
export type Detail = Weakness & {
  lesson: Lesson | null;
  mastery_requirements_vi: string;
  evidence: {
    id: string;
    skill: string;
    attempt_id: string;
    original_text: string | null;
    corrected_text: string | null;
    outcome: string;
    created_at: string;
    details: {
      source_url: string;
      explanation_vi?: string;
      audible_evidence_vi?: string;
      part?: number;
      selected_answer?: string;
      correct_answer?: string;
    };
  }[];
};
export type Weekly = {
  attempts_completed: number;
  recorded_practice_minutes: number;
  new_weaknesses: number;
  improving: number;
  mastered: number;
  highest_improvement: string | null;
  next_priority: string | null;
  ai_summary: WeeklySummary | null;
};
export type WeeklySummary = {
  summary_vi: string;
  recommendations: {
    weakness_id: string;
    label_vi: string;
    reason_vi: string;
    activity_vi: string;
    url: string;
  }[];
  created_at: string;
};
export type Overview = {
  backfill_status: string;
  backfill_processed: number;
  revision: number;
  recent: {
    writing_attempts: number;
    speaking_attempts: number;
    reading_questions: number;
  };
  top_priorities: Weakness[];
  improving_skills: number;
  mastered_count: number;
  strengths: {
    skill: string;
    label: string;
    value: number;
    unit: string;
    evidence_count: number;
    trend: string;
  }[];
  weekly: Weekly;
  priority_note_vi: string;
};
export type SkillAnalysis = {
  skill: Skill;
  criteria: {
    criterion: string;
    recent_average: number | null;
    older_average: number | null;
    samples: number;
    trend: string;
  }[];
  weaknesses: Weakness[];
  audio_note_vi?: string;
  question_types?: {
    concept_key: string;
    label: string;
    total: number;
    correct: number;
    incorrect: number;
    accuracy: number;
  }[];
};
export type VocabularyAnalysis = {
  weaknesses: Weakness[];
  frequent_expressions: { phrase: string; count: number; attempts: number }[];
  frequency_note_vi: string;
  notebook: {
    id: string;
    phrase: string;
    mastery_level: string;
    review_count: number;
    observed_reuses: number;
    verified_reuses: number;
    pending_verifications: string[];
    skills: string[];
    learned_not_reused: boolean;
  }[];
};
export type PlanItem = {
  id: string;
  date: string;
  skill: Skill;
  concept_key: string;
  weakness_id: string;
  activity_type: string;
  estimated_minutes: number;
  status: string;
  title: string;
  url: string;
  reason_vi: string;
  exercise_count: number;
};
export type Plan = {
  id: string;
  duration_days: number;
  daily_minutes: number;
  start_date: string;
  end_date: string;
  status: string;
  items: PlanItem[];
};
export type Today = {
  date: string;
  items: PlanItem[];
  recommendations: {
    weakness_id: string;
    title: string;
    skill: Skill;
    estimated_minutes: number;
    url: string;
    reason_vi: string;
  }[];
  estimated_minutes: number;
  plan_id: string | null;
};
export type Exercise = {
  id: string;
  weakness_id: string;
  concept_key: string;
  title: string;
  completed_at: string | null;
  answered_count: number;
  correct_count: number;
  items: {
    kind: string;
    instruction_vi: string;
    text: string;
    options: string[];
    passage: string | null;
    target_words: string[];
    seconds: number | null;
    evaluation: string;
    result?: {
      answer: string;
      correct: boolean | null;
      feedback: { explanation_vi: string; suggested_answer?: string };
    };
  }[];
};
export const statusLabels: Record<string, string> = {
  NEW: "Mới ghi nhận",
  OBSERVED: "Đang theo dõi",
  RECURRING: "Lặp lại",
  LEARNING: "Đang học",
  IMPROVING: "Đang cải thiện",
  MASTERED: "Đã thành thạo",
  REGRESSED: "Cần ôn lại",
  NOT_STARTED: "Chưa bắt đầu",
  PRACTICING: "Đang luyện",
};
export const trends: Record<string, string> = {
  IMPROVING: "Đang cải thiện",
  STABLE: "Chưa thay đổi rõ",
  DECLINING: "Cần chú ý",
  INSUFFICIENT_DATA: "Chưa đủ dữ liệu so sánh",
};
export const criteria: Record<string, string> = {
  task_fulfillment: "Đáp ứng yêu cầu",
  organization: "Tổ chức bài",
  vocabulary: "Từ vựng",
  grammar: "Ngữ pháp",
  pronunciation: "Phát âm",
  fluency: "Độ trôi chảy",
  structures: "Triển khai và liên kết ý",
};
export const kinds: Record<string, string> = {
  MULTIPLE_CHOICE: "Trắc nghiệm",
  FILL_BLANK: "Điền chỗ trống",
  ERROR_CORRECTION: "Sửa lỗi",
  SENTENCE_TRANSFORMATION: "Biến đổi câu",
  COLLOCATION: "Kết hợp từ",
  NATURAL_EXPRESSION: "Chọn diễn đạt tự nhiên",
  REWRITE_SENTENCE: "Viết lại câu",
  CONTEXTUAL_GAP: "Điền từ theo ngữ cảnh",
  ACTIVE_RECALL: "Nhớ lại cụm từ",
  FIX_SENTENCE: "Chữa câu",
  IMPROVE_PARAGRAPH: "Cải thiện đoạn văn",
  WRITE_INTRODUCTION: "Viết mở bài",
  DEVELOP_IDEA: "Phát triển một ý",
  MINI_TASK1: "Mini Task 1",
  MINI_TASK2: "Đoạn văn Task 2",
  READING_TARGETED: "Đọc theo loại câu",
  SHORT_ANSWER: "Trả lời ngắn",
  SENTENCE_EXPANSION: "Mở rộng câu nói",
  TIMED_RESPONSE: "Nói có giới hạn thời gian",
  PRONUNCIATION_WORDS: "Luyện phát âm",
  REUSE_VOCABULARY: "Dùng từ đã học khi nói",
  PART2_COMPARISON: "So sánh lựa chọn Part 2",
  PART3_DEVELOPMENT: "Phát triển ý Part 3",
};
export const allowedKinds: Record<string, string[]> = {
  GRAMMAR: [
    "MULTIPLE_CHOICE",
    "FILL_BLANK",
    "ERROR_CORRECTION",
    "SENTENCE_TRANSFORMATION",
  ],
  VOCABULARY: [
    "COLLOCATION",
    "NATURAL_EXPRESSION",
    "REWRITE_SENTENCE",
    "CONTEXTUAL_GAP",
    "ACTIVE_RECALL",
  ],
  WRITING: [
    "FIX_SENTENCE",
    "IMPROVE_PARAGRAPH",
    "WRITE_INTRODUCTION",
    "DEVELOP_IDEA",
    "REWRITE_SENTENCE",
    "MINI_TASK1",
    "MINI_TASK2",
  ],
  READING: ["READING_TARGETED"],
  SPEAKING: [
    "SHORT_ANSWER",
    "SENTENCE_EXPANSION",
    "TIMED_RESPONSE",
    "REUSE_VOCABULARY",
    "PART2_COMPARISON",
    "PART3_DEVELOPMENT",
  ],
  PRONUNCIATION: ["PRONUNCIATION_WORDS"],
};
