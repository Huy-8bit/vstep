import type { TestProfile } from "@/lib/test-profile";
export type ReadingMode =
  | "FULL_TEST"
  | "PASSAGE_PRACTICE"
  | "QUICK_PRACTICE"
  | "QUESTION_TYPE_PRACTICE";
export type Option = "A" | "B" | "C" | "D";
export const options: Option[] = ["A", "B", "C", "D"];
export const modes: Record<
  ReadingMode,
  { title: string; description: string; meta: string }
> = {
  FULL_TEST: {
    title: "Thi thử Reading",
    description:
      "Bốn bài đọc, 40 câu hỏi. Tập trung như trong phòng thi và chủ động phân bổ thời gian.",
    meta: "40 câu · 60 phút",
  },
  PASSAGE_PRACTICE: {
    title: "Luyện một passage",
    description:
      "Đọc kỹ một bài, tìm bằng chứng và hiểu cách phân biệt các phương án.",
    meta: "10 câu · Tùy chọn thời gian",
  },
  QUICK_PRACTICE: {
    title: "Luyện nhanh",
    description:
      "Một lượt đọc ngắn với năm câu hỏi để giữ nhịp luyện tập mỗi ngày.",
    meta: "5 câu · Khoảng 8 phút",
  },
  QUESTION_TYPE_PRACTICE: {
    title: "Luyện theo dạng câu",
    description:
      "Tập trung vào dạng câu hỏi bạn muốn cải thiện, chọn từ những bài trong ngân hàng.",
    meta: "Tối đa 5 câu cùng dạng",
  },
};
export const questionTypes: Record<string, string> = {
  main_idea: "Main Idea",
  detail: "Detail",
  inference: "Inference",
  vocabulary: "Vocabulary in Context",
  reference: "Reference",
  purpose: "Author’s Purpose",
  negative_detail: "Negative Detail / Except",
  sentence_meaning: "Sentence Meaning",
  organization: "Organization",
  tone: "Tone / Attitude",
};
export const topics: Record<string, string> = {
  random: "Chủ đề ngẫu nhiên",
  education: "Giáo dục",
  technology: "Công nghệ",
  environment: "Môi trường",
  health: "Sức khỏe",
  science: "Khoa học",
  society: "Xã hội",
  culture: "Văn hóa",
  work: "Công việc",
  business: "Kinh doanh",
  travel: "Du lịch",
  psychology: "Tâm lý học",
  history: "Lịch sử",
  communication: "Giao tiếp",
  nature: "Thiên nhiên",
  lifestyle: "Lối sống",
};
export type ReadingQuestion = {
  id: string;
  passage_id: string;
  question_number: number;
  question_type: string;
  question_text: string;
  options: Record<Option, string>;
};
export type ReadingPassage = {
  id: string;
  title: string;
  topic: string;
  test_profile: TestProfile;
  paragraphs: { id: string; text: string }[];
  word_count: number;
  source: string;
  questions: ReadingQuestion[];
};
export type ReadingAnswer = {
  question_id: string;
  selected_answer: Option | null;
  is_marked_for_review: boolean;
  revision: number;
  time_spent_seconds: number;
  answered_at: string | null;
  updated_at: string;
};
export type ReadingSession = {
  id: string;
  mode: ReadingMode;
  test_profile: TestProfile;
  topic: string;
  started_at: string;
  expires_at: string | null;
  submitted_at: string | null;
  status: string;
  question_count: number;
  question_ids: string[];
  server_now: string;
  passages: ReadingPassage[];
  answers: ReadingAnswer[];
};
export type Breakdown = {
  key: string;
  total: number;
  correct: number;
  answered: number;
  accuracy: number;
  time_spent_seconds: number;
};
export type ReviewQuestion = ReadingQuestion &
  ReadingAnswer & {
    is_correct: boolean | null;
    correct_answer: Option;
    explanation_vi: string;
    option_explanations: Record<
      Option,
      { is_correct: boolean; explanation_vi: string }
    >;
    evidence: { paragraph_id: string; quote: string };
  };
export type ReadingResult = {
  session: ReadingSession;
  result: {
    id: string;
    correct_count: number;
    incorrect_count: number;
    unanswered_count: number;
    accuracy: number;
    score: number;
    duration_seconds: number;
    question_type_breakdown: Breakdown[];
    passage_breakdown: Breakdown[];
    strategy_feedback: {
      kind: string;
      title_vi: string;
      explanation_vi: string;
      question_type: string | null;
    }[];
  };
  review: ReviewQuestion[];
};
export type ReadingProgress = {
  completed_sessions: number;
  questions_total: number;
  questions_answered: number;
  correct_count: number;
  accuracy: number | null;
  average_score: number | null;
  average_time_per_question: number | null;
  question_types: Breakdown[];
  topics: Breakdown[];
  weaknesses: Breakdown[];
  timeline: {
    id: string;
    date: string;
    mode: ReadingMode;
    score: number;
    accuracy: number;
  }[];
};
export type Bank = {
  test_profile: TestProfile;
  full_test_missing_passages: number;
  ai_configured: boolean;
  items: {
    id: string;
    title: string;
    topic: string;
    test_profile: TestProfile;
    word_count: number;
    question_count: number;
    question_types: string[];
    source: string;
  }[];
};
export type Vocabulary = {
  term: string;
  meaning_vi: string;
  part_of_speech: string;
  meaning_in_context: string;
  example: string;
  synonyms: string[];
};
export const duration = (seconds: number) =>
  `${Math.floor(Math.max(0, seconds) / 60)}:${Math.floor(
    Math.max(0, seconds) % 60,
  )
    .toString()
    .padStart(2, "0")}`;
export const disclaimer =
  "Điểm luyện tập tham khảo = số câu đúng / tổng số câu × 10; không phải điểm quy đổi chính thức của kỳ thi VSTEP.";
