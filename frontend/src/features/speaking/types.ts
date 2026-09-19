import type { LibraryMetadata } from "@/features/library/types";
import type { AudioAssessment } from "./pronunciation-types";
import type { TestProfile } from "@/lib/test-profile";
export type SpeakingMode =
  "FULL_TEST" | "PART1" | "PART2" | "PART3" | "QUICK_PRACTICE";
export const modes: Record<
  SpeakingMode,
  { title: string; subtitle: string; description: string; time: string }
> = {
  FULL_TEST: {
    title: "Thi thử Speaking",
    subtitle: "Full Speaking Test",
    description:
      "Trải nghiệm trọn vẹn ba phần và câu hỏi follow-up. Một lần ghi âm cho mỗi câu trả lời.",
    time: "Khoảng 12 phút",
  },
  PART1: {
    title: "Luyện Part 1",
    subtitle: "Social Interaction",
    description:
      "Trò chuyện về hai chủ đề quen thuộc qua 3–6 câu hỏi, nhận phản hồi sau mỗi câu.",
    time: "Khoảng 3 phút · Hai chủ đề",
  },
  PART2: {
    title: "Luyện Part 2",
    subtitle: "Solution Discussion",
    description:
      "Chọn một trong ba phương án, giải thích lý do và thảo luận lựa chọn còn lại.",
    time: "Khoảng 4 phút",
  },
  PART3: {
    title: "Luyện Part 3",
    subtitle: "Topic Development",
    description:
      "Phát triển chủ đề từ các ý gợi ý, thêm ý riêng và trả lời follow-up.",
    time: "Khoảng 5 phút",
  },
  QUICK_PRACTICE: {
    title: "Luyện nhanh",
    subtitle: "A little practice, every day",
    description: "Một câu hỏi ngẫu nhiên để khởi động khả năng nói tiếng Anh.",
    time: "1–2 phút",
  },
};
export const topics: Record<string, string> = {
  random: "Chủ đề ngẫu nhiên",
  education: "Giáo dục",
  family: "Gia đình",
  travel: "Du lịch",
  shopping: "Mua sắm",
  health: "Sức khỏe",
  work: "Công việc",
  technology: "Công nghệ",
  leisure: "Giải trí",
  community: "Cộng đồng",
  transportation: "Giao thông",
  environment: "Môi trường",
  social_activities: "Hoạt động xã hội",
  books: "Sách",
  sports: "Thể thao",
  holidays: "Ngày lễ",
  study: "Học tập",
  career: "Sự nghiệp",
  food: "Ẩm thực",
  films: "Phim ảnh",
  hometown: "Quê hương",
  friends: "Bạn bè",
  music: "Âm nhạc",
  daily_life: "Cuộc sống",
};
export const criterionLabels = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  pronunciation: "Pronunciation",
  fluency: "Fluency",
  structures: "Coherence & Cohesion",
};
export type Criterion = keyof typeof criterionLabels;
export type Improvement = {
  title_vi: string;
  explanation_vi: string;
  example: string;
};
export type SpeakingQuestion = {
  id: string;
  part: number;
  question_type: string;
  topic: string;
  question_text: string;
  topic_sets: { topic: string; questions: string[] }[];
  situation: string | null;
  options: string[];
  suggested_ideas: string[];
  follow_up_questions: string[];
  test_profile: TestProfile;
  source: string;
};
export type Step = {
  practice_seconds?: number;
  optional_context?: string;
  practice_asset_ids?: string[];
  sequence_number: number;
  question_id: string;
  part: number;
  kind: "interaction" | "solution" | "main_talk" | "follow_up";
  topic: string;
  topic_code: string;
  question_text: string;
  situation: string | null;
  options: string[];
  suggested_ideas: string[];
  allow_own_idea: boolean;
};
export type SpeakingError = {
  id: string;
  sequence_number: number;
  category: string;
  subtype: string;
  original: string;
  corrected: string;
  explanation_vi: string;
  severity: string;
  confidence: number | null;
};
export type SpeakingGrading = {
  id: string;
  scores: Record<Criterion | "overall", number | null>;
  estimated_level: string;
  summary_vi: string;
  strengths: string[];
  priority_improvements: Improvement[];
  content_feedback: Improvement[];
  fluency_feedback: Improvement[];
  structure_feedback: Improvement[];
  speaking_frame: Improvement[];
  errors: SpeakingError[];
  pronunciation_feedback: {
    sequence_number: number;
    word: string;
    issue: string;
    feedback_vi: string;
    ipa: string | null;
    suggestion: string;
    confidence: number;
  }[];
  vocabulary_suggestions: {
    sequence_number: number;
    original: string;
    suggestion: string;
    reason_vi: string;
    example: string;
  }[];
  sentence_corrections: {
    sequence_number: number;
    original: string;
    corrected: string;
    explanation_vi: string;
    start_seconds: number | null;
  }[];
  answer_feedback: {
    sequence_number: number;
    part: number;
    summary_vi: string;
    best_option_clearly_stated: boolean | null;
    reasons_developed_vi: string;
    other_options_discussed_vi: string;
    corrected_transcript: string;
    improved_b2_answer: string;
  }[];
  corrected_transcript: string;
  improved_b2_answer: string;
  audio_coverage: {
    recordings: number;
    analyzed: number;
    complete: boolean;
    pronunciation_confidence: number;
    fluency_confidence: number;
  };
};
export type SpeakingAnswer = {
  id: string;
  session_id: string;
  sequence_number: number;
  part: number;
  question_text: string;
  status: string;
  audio_duration_ms: number | null;
  mime_type: string | null;
  audio_size: number | null;
  has_audio: boolean;
  audio_url: string | null;
  transcript: string | null;
  word_count: number | null;
  metrics: Record<string, number | string | null>;
  audio_analysis: AudioAssessment | null;
  grading: SpeakingGrading | null;
};
export type SpeakingSession = LibraryMetadata & {
  id: string;
  mode: SpeakingMode;
  started_at: string;
  completed_at: string | null;
  status: string;
  current_part: number;
  current_sequence: number;
  current_question: Step | null;
  total_questions: number;
  visible_questions: Step[];
  answers: SpeakingAnswer[];
  grading: SpeakingGrading | null;
  server_now: string;
  suggested_duration_seconds: number | null;
  part_timings: Record<string, number>;
  limits: { max_audio_mb: number; max_audio_seconds: number };
  audio_analysis_configured: boolean;
  tts_configured: boolean;
};
export const duration = (seconds: number) =>
  `${Math.floor(seconds / 60)}:${Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0")}`;
export const scoreText = (n: number | null | undefined) =>
  n == null ? "—" : n.toFixed(1);
export const disclaimer =
  "Kết quả được AI ước tính nhằm phục vụ luyện tập và không phải điểm Speaking chính thức của kỳ thi VSTEP.";
