import { topics as writingTopics } from "@/lib/constants";
import { topics as speakingTopics } from "@/features/speaking/types";
import { topics as readingTopics } from "@/features/reading/types";
export const topicLabels: Record<string, string> = {
  ...readingTopics,
  ...speakingTopics,
  ...writingTopics,
};
export type Skill = "WRITING" | "SPEAKING" | "READING";
export type ReviewKind = "RECALL" | "GAP" | "COLLOCATION" | "CORRECT" | "USE";
export const reviewKinds: Record<ReviewKind, string> = {
  RECALL: "Nhớ cụm từ",
  GAP: "Điền chỗ trống",
  COLLOCATION: "Chọn collocation",
  CORRECT: "Sửa câu cũ",
  USE: "Đặt câu mới",
};
export const masteryLabels: Record<string, string> = {
  NEW: "Mới",
  LEARNING: "Đang học",
  FAMILIAR: "Đã quen",
  MASTERED: "Đã nhớ",
};
export const issueLabels: Record<string, string> = {
  word_choice: "Chọn từ",
  collocation: "Collocation",
  word_form: "Dạng từ",
  countability: "Danh từ đếm được",
  register: "Sắc thái",
  lexical_gap: "Thiếu cách diễn đạt",
  word_family: "Họ từ",
};
export type LearningItem = {
  headword: string;
  phrase: string;
  part_of_speech: string;
  meaning_vi: string;
  meaning_in_context_vi: string;
  register: string;
  collocations: string[];
  common_patterns: string[];
  example_sentence: string;
  why_learn_this_vi: string;
  issue_type: string;
  priority: string;
};
export type Suggestion = LearningItem & {
  index: number;
  saved_item_id: string | null;
  source_type: string;
  user_original: string;
  better_version: string;
  natural_options: string[];
};
export type Batch = { batch_id: string | null; items: Suggestion[] };
export type Source = {
  source_skill: Skill;
  source_attempt_id: string;
  passage_id?: string;
  paragraph_id?: string;
  term?: string;
};
export type VocabularyItem = LearningItem & {
  id: string;
  source_skill: Skill;
  source_attempt_id: string;
  source_topic: string;
  user_original_text: string | null;
  improved_text: string | null;
  mastery_level: string;
  review_count: number;
  correct_review_count: number;
  last_reviewed_at: string | null;
  next_review_at: string | null;
  created_at: string;
};
export type VocabularyProgress = {
  total: number;
  learned: number;
  mastered: number;
  due: number;
  reviews: number;
  correct_reviews: number;
  mastery: Record<string, number>;
  source_counts: Record<string, number>;
  recurring_errors: { issue_type: string; original: string; count: number }[];
  issue_trends: {
    issue_type: string;
    reviews: number;
    recent_accuracy: number;
    trend: string;
  }[];
  most_practiced_topics: { topic: string; count: number }[];
};
export type Review = {
  id: string;
  item_id: string;
  kind: ReviewKind;
  prompt: {
    instruction_vi: string;
    text: string;
    context: string;
    options: string[];
  };
  answer: string | null;
  correct: boolean | null;
  assessed_at: string | null;
  feedback: null | {
    explanation_vi: string;
    suggested_answer: string;
    example_sentence: string;
    mastery_level: string;
    next_review_at: string | null;
    progression_applied: boolean;
    confidence: number;
    assessment: string;
  };
};
export const sourceLink = (item: VocabularyItem) =>
  item.source_skill === "WRITING"
    ? `/result?id=${item.source_attempt_id}`
    : `/${item.source_skill.toLowerCase()}/result?id=${item.source_attempt_id}`;
