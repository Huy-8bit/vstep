export type Skill = "writing" | "speaking" | "reading";
export type LibraryPart =
  | "task_1"
  | "task_2"
  | "part_1"
  | "part_2"
  | "part_3"
  | "passage"
  | "mini"
  | "full";
export type KeySource =
  "provided" | "user_confirmed" | "ai_suggested" | "unknown";
export type Letter = "A" | "B" | "C" | "D";
export type WritingItem = {
  task_type: 1 | 2;
  instruction: string;
  stimulus_type: string;
  stimulus_text: string;
  requirements: string[];
  minimum_words: number | null;
  essay_family: string;
};
export type SpeakingItem = {
  part: 1 | 2 | 3;
  topic: string;
  topic_sets: { topic: string; questions: string[] }[];
  situation: string;
  options: string[];
  candidate_task: string;
  optional_context: string;
  central_idea: string;
  suggested_ideas: string[];
  follow_up_questions: string[];
};
export type ReadingItemQuestion = {
  question_number: number;
  question_text: string;
  question_type: string;
  options: Record<Letter, string>;
  correct_answer: Letter | null;
  answer_key_source: KeySource;
  answer_key_evidence: string | null;
  explanation: string | null;
};
export type ReadingItem = {
  title: string;
  passage_text: string;
  questions: ReadingItemQuestion[];
};
export type LibraryContent = {
  practice_asset_ids?: string[];
  writing: WritingItem[];
  speaking: SpeakingItem[];
  reading: ReadingItem[];
};
export type LibraryDocument = {
  title: string;
  skill: Skill;
  part: LibraryPart;
  topic: string;
  tags: string[];
  favorite: boolean;
  collection_id: string | null;
  source_type: string;
  source_name: string | null;
  source_url: string | null;
  notes: string | null;
  asset_ids: string[];
  content: LibraryContent;
};
export type LibraryMetadata = {
  library_question_id?: string | null;
  library_revision?: number | null;
  library_title?: string | null;
};
export type LibraryRow = {
  id: string;
  revision: number;
  created_at: string;
  updated_at: string;
  origin: string;
  document: LibraryDocument;
  practice_issues: string[];
  answer_key: { trusted: number; total: number; complete: boolean };
  stats: {
    attempt_count: number;
    last_practiced: string | null;
    latest_score: number | null;
    best_score: number | null;
  };
};
export type Collection = { id: string; name: string };
export type ParsedItem = {
  document: LibraryDocument;
  confidence: { skill: number; part: number; answer_key: number | null };
  warnings: string[];
};
export type ParsedImport = { items: ParsedItem[]; warnings: string[] };
export const skillLabels: Record<Skill, string> = {
  writing: "Writing",
  speaking: "Speaking",
  reading: "Reading",
};
export const partLabels: Record<LibraryPart, string> = {
  task_1: "Task 1",
  task_2: "Task 2",
  part_1: "Part 1",
  part_2: "Part 2",
  part_3: "Part 3",
  passage: "Một bài đọc",
  mini: "Reading mini",
  full: "Bài thi đầy đủ",
};
export const parts: Record<Skill, LibraryPart[]> = {
  writing: ["task_1", "task_2", "full"],
  speaking: ["part_1", "part_2", "part_3", "full"],
  reading: ["passage", "mini", "full"],
};
export const keyLabels: Record<KeySource, string> = {
  provided: "Từ nguồn đề",
  user_confirmed: "Bạn đã xác nhận",
  ai_suggested: "AI đề xuất · chưa xác nhận",
  unknown: "Chưa có đáp án",
};
export const emptyWriting = (task_type: 1 | 2): WritingItem => ({
  task_type,
  instruction: "",
  stimulus_type: "other",
  stimulus_text: "",
  requirements: [],
  minimum_words: null,
  essay_family: "other",
});
export const emptySpeaking = (part: 1 | 2 | 3): SpeakingItem => ({
  part,
  topic: "",
  topic_sets: part === 1 ? [{ topic: "", questions: [] }] : [],
  situation: "",
  options: part === 2 ? ["", "", ""] : [],
  candidate_task: "",
  optional_context: "",
  central_idea: "",
  suggested_ideas: [],
  follow_up_questions: [],
});
export const emptyReadingQuestion = (number: number): ReadingItemQuestion => ({
  question_number: number,
  question_text: "",
  question_type: "other",
  options: { A: "", B: "", C: "", D: "" },
  correct_answer: null,
  answer_key_source: "unknown",
  answer_key_evidence: null,
  explanation: null,
});
export const emptyReading = (): ReadingItem => ({
  title: "",
  passage_text: "",
  questions: [emptyReadingQuestion(1)],
});
export function configure(
  document: LibraryDocument,
  skill: Skill,
  part: LibraryPart,
): LibraryDocument {
  const previous =
    document.skill === skill
      ? document.content
      : { writing: [], speaking: [], reading: [] };
  const content: LibraryContent = {
    writing: [],
    speaking: [],
    reading: [],
    practice_asset_ids: document.content.practice_asset_ids || [],
  };
  if (skill === "writing")
    content.writing = (part === "full" ? [1, 2] : [Number(part.at(-1))]).map(
      (n) =>
        previous.writing.find((q) => q.task_type === n) ||
        emptyWriting(n as 1 | 2),
    );
  if (skill === "speaking")
    content.speaking = (
      part === "full" ? [1, 2, 3] : [Number(part.at(-1))]
    ).map(
      (n) =>
        previous.speaking.find((q) => q.part === n) ||
        emptySpeaking(n as 1 | 2 | 3),
    );
  if (skill === "reading")
    content.reading =
      part === "full"
        ? Array.from(
            { length: 4 },
            (_, i) => previous.reading[i] || emptyReading(),
          )
        : part === "passage"
          ? [previous.reading[0] || emptyReading()]
          : previous.reading.length
            ? previous.reading
            : [emptyReading()];
  return { ...document, skill, part, content };
}
export function emptyDocument(): LibraryDocument {
  return {
    title: "",
    skill: "writing",
    part: "task_1",
    topic: "other",
    tags: [],
    favorite: false,
    collection_id: null,
    source_type: "manual",
    source_name: null,
    source_url: null,
    notes: null,
    asset_ids: [],
    content: { writing: [emptyWriting(1)], speaking: [], reading: [] },
  };
}
