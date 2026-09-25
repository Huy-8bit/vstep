"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FilePlus2, FileUp, Sparkles } from "lucide-react";
import { api, post } from "@/services/api";
import {
  ActionMenu,
  ConfirmDialog,
  DataTable,
  EmptyState,
  ErrorState,
  FilterBar,
  Notice,
  PageHeader,
  Pagination,
  SearchInput,
  Section,
  StatusBadge,
  cellClass,
  fmtDate,
  fmtNumber,
  inputClass,
  primaryClass,
  secondaryClass,
  dangerClass,
  useAdminData,
  type ListResponse,
} from "./admin-ui";

type Question = {
  id: string;
  skill: string;
  title: string;
  part: number | string;
  topic: string;
  source: string;
  access_tier: string;
  is_published: boolean;
  available_for_free_trial: boolean;
  is_featured: boolean;
  quality_valid: boolean;
  attempts: number;
  created_at: string;
};
type Draft = {
  id: string;
  title: string;
  skill: string;
  part: string;
  updated_at: string;
  imported_count: number;
};
type Detail = Question & {
  content: Record<string, unknown>;
  questions?: {
    id: string;
    question_number: number;
    question_type: string;
    question_text: string;
    options: Record<string, string> | string[];
    correct_answer: string | null;
    answer_key_source: string;
  }[];
};
const skillLabel: Record<string, string> = {
  writing: "Writing",
  speaking: "Speaking",
  reading: "Reading",
};
const status = (question: Question) =>
  question.access_tier === "INTERNAL"
    ? "INTERNAL"
    : question.is_published
      ? "PUBLISHED"
      : "DRAFT";

export function QuestionsPanel() {
  const router = useRouter(),
    params = useSearchParams();
  const page = Math.max(1, Number(params.get("page") || 1)),
    pageSize = 25,
    search = params.get("search") || "";
  const [draftSearch, setDraftSearch] = useState(search),
    [notice, setNotice] = useState(""),
    [busyId, setBusyId] = useState("");
  const [generateOpen, setGenerateOpen] = useState(false),
    [aiSkill, setAiSkill] = useState("writing"),
    [aiPart, setAiPart] = useState(1);
  const [archive, setArchive] = useState<Question | null>(null);
  function update(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value && value !== "all") next.set(key, value);
    else next.delete(key);
    next.delete("page");
    router.replace("/admin/questions?" + next.toString());
  }
  const path =
    "/admin/questions?" +
    new URLSearchParams({
      skill: params.get("skill") || "all",
      publication: params.get("publication") || "all",
      search,
      source: params.get("source") || "all",
      access_tier: params.get("access_tier") || "all",
      part: params.get("part") || "all",
      topic: params.get("topic") || "",
      sort: params.get("sort") || "created_desc",
      offset: String((page - 1) * pageSize),
      limit: String(pageSize),
    });
  const { data, error, setError, loading, reload } =
    useAdminData<ListResponse<Question>>(path);
  const drafts = useAdminData<ListResponse<Draft>>(
    "/admin/question-drafts?limit=10",
  );
  async function importDraft(id: string) {
    setBusyId(id);
    try {
      await post("/admin/question-drafts/" + id + "/to-bank");
      setNotice("Đã đưa bản soạn vào ngân hàng dưới dạng nháp.");
      reload();
      drafts.reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusyId("");
    }
  }
  async function generateDraft() {
    setBusyId("ai");
    try {
      const route =
        aiSkill === "writing"
          ? "/questions/generate"
          : aiSkill === "speaking"
            ? "/speaking/questions/generate"
            : "/reading/questions/generate";
      const payload =
        aiSkill === "writing"
          ? { task: aiPart, source: "AI" }
          : aiSkill === "speaking"
            ? { part: aiPart, source: "AI" }
            : { mode: "PASSAGE_PRACTICE", question_count: 10 };
      await post(route, payload);
      setGenerateOpen(false);
      setNotice("Đã tạo bản nháp AI. Hãy duyệt trước khi xuất bản.");
      update("skill", aiSkill);
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusyId("");
    }
  }
  async function archiveQuestion() {
    if (!archive) return;
    setBusyId(archive.id);
    try {
      await api("/admin/questions/" + archive.skill + "/" + archive.id, {
        method: "DELETE",
      });
      setNotice("Đã lưu trữ đề.");
      setArchive(null);
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusyId("");
    }
  }
  return (
    <div>
      <PageHeader
        title="Ngân hàng đề"
        description="Duyệt, xuất bản và quản lý đề Writing, Speaking, Reading."
        action={
          <div className="flex flex-wrap gap-2">
            <Link href="/my-questions/new" className={primaryClass}>
              <FilePlus2 size={15} /> Thêm đề
            </Link>
            <Link href="/my-questions/new" className={secondaryClass}>
              <FileUp size={15} /> Nhập PDF / ảnh
            </Link>
            <button
              className={secondaryClass}
              onClick={() => setGenerateOpen(true)}
            >
              <Sparkles size={15} /> Sinh bằng AI
            </button>
          </div>
        }
      />
      <Notice text={notice} onClose={() => setNotice("")} />
      <ErrorState
        message={error || drafts.error}
        retry={() => {
          reload();
          drafts.reload();
        }}
      />
      <div className="mb-4 flex gap-1 overflow-x-auto border-b border-slate-200">
        {[
          ["all", "Tất cả"],
          ["writing", "Writing"],
          ["speaking", "Speaking"],
          ["reading", "Reading"],
        ].map(([key, label]) => (
          <button
            key={key}
            className={
              "whitespace-nowrap border-b-2 px-4 py-2.5 text-sm " +
              ((params.get("skill") || "all") === key
                ? "border-teal-700 font-semibold text-teal-800"
                : "border-transparent text-slate-500")
            }
            onClick={() => update("skill", key)}
          >
            {label}
          </button>
        ))}
      </div>
      <FilterBar>
        <form
          className="flex min-w-52 flex-[2] gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            update("search", draftSearch.trim());
          }}
        >
          <SearchInput
            value={draftSearch}
            onChange={setDraftSearch}
            placeholder="Tìm nội dung đề"
          />
          <button className={secondaryClass}>Tìm</button>
        </form>
        <select
          aria-label="Trạng thái đề"
          className={inputClass}
          value={params.get("publication") || "all"}
          onChange={(event) => update("publication", event.target.value)}
        >
          <option value="all">Mọi trạng thái</option>
          <option value="published">Đã xuất bản</option>
          <option value="draft">Bản nháp</option>
          <option value="archived">Đã lưu trữ</option>
        </select>
        <select
          aria-label="Phần thi"
          className={inputClass}
          value={params.get("part") || "all"}
          onChange={(event) => update("part", event.target.value)}
        >
          <option value="all">Mọi phần</option>
          {[1, 2, 3].map((value) => (
            <option key={value} value={value}>
              Task / Part {value}
            </option>
          ))}
        </select>
        <select
          aria-label="Quyền truy cập"
          className={inputClass}
          value={params.get("access_tier") || "all"}
          onChange={(event) => update("access_tier", event.target.value)}
        >
          <option value="all">Mọi tầng</option>
          <option value="FREE_TRIAL">Trial</option>
          <option value="VIP">VIP</option>
          <option value="INTERNAL">Nội bộ</option>
        </select>
        <select
          aria-label="Nguồn đề"
          className={inputClass}
          value={params.get("source") || "all"}
          onChange={(event) => update("source", event.target.value)}
        >
          <option value="all">Mọi nguồn</option>
          <option value="SEED">Đề mẫu</option>
          <option value="AI">AI</option>
          <option value="CUSTOM">Nhập tay</option>
          <option value="IMPORTED">Nhập từ tệp</option>
        </select>
        <select
          aria-label="Sắp xếp"
          className={inputClass}
          value={params.get("sort") || "created_desc"}
          onChange={(event) => update("sort", event.target.value)}
        >
          <option value="created_desc">Mới nhất</option>
          <option value="created_asc">Cũ nhất</option>
          <option value="attempts_desc">Nhiều lượt luyện</option>
        </select>
        <button
          className={secondaryClass}
          onClick={() => {
            setDraftSearch("");
            router.replace("/admin/questions");
          }}
        >
          Xóa lọc
        </button>
      </FilterBar>
      <DataTable
        headers={[
          "Đề",
          "Kỹ năng",
          "Phần",
          "Chủ đề",
          "Nguồn",
          "Truy cập",
          "Trạng thái",
          "Lượt luyện",
          "Tạo lúc",
          "",
        ]}
        loading={loading}
        minWidth={1180}
        empty={
          !data?.items.length && (
            <EmptyState
              title="Không tìm thấy đề"
              description="Thử đổi bộ lọc hoặc thêm đề mới."
              action={
                <Link href="/my-questions/new" className={secondaryClass}>
                  Thêm đề đầu tiên
                </Link>
              }
            />
          )
        }
      >
        {data?.items.map((item) => (
          <tr key={item.id} className="hover:bg-slate-50/70">
            <td className={cellClass}>
              <Link
                href={"/admin/question?skill=" + item.skill + "&id=" + item.id}
                className="block max-w-80 truncate font-medium text-teal-800"
                title={item.title}
              >
                {item.title}
              </Link>
            </td>
            <td className={cellClass}>{skillLabel[item.skill]}</td>
            <td className={cellClass}>
              {item.skill === "reading"
                ? "Bài đọc"
                : item.skill === "writing"
                  ? "Task " + item.part
                  : "Part " + item.part}
            </td>
            <td className={cellClass}>
              <span className="block max-w-28 truncate" title={item.topic}>
                {item.topic}
              </span>
            </td>
            <td className={cellClass}>
              {(
                {
                  SEED: "Đề mẫu",
                  AI: "AI",
                  CUSTOM: "Thủ công",
                  IMPORTED: "Đã nhập",
                } as Record<string, string>
              )[item.source] || item.source}
            </td>
            <td className={cellClass}>
              <StatusBadge status={item.access_tier} />
            </td>
            <td className={cellClass}>
              <StatusBadge status={status(item)} />
            </td>
            <td className={cellClass}>{fmtNumber(item.attempts)}</td>
            <td className={cellClass}>{fmtDate(item.created_at)}</td>
            <td className={cellClass}>
              <ActionMenu
                actions={[
                  {
                    label: "Xem / chỉnh sửa",
                    onClick: () =>
                      router.push(
                        "/admin/question?skill=" + item.skill + "&id=" + item.id,
                      ),
                  },
                  {
                    label: "Lưu trữ",
                    onClick: () => setArchive(item),
                    danger: true,
                  },
                ]}
              />
            </td>
          </tr>
        ))}
      </DataTable>
      <Pagination
        page={page}
        pageSize={pageSize}
        total={data?.total || 0}
        onPage={(value) => {
          const next = new URLSearchParams(params.toString());
          next.set("page", String(value));
          router.replace("/admin/questions?" + next.toString());
        }}
      />
      <Section
        title="Bản soạn của admin"
        action={
          <Link
            href="/my-questions"
            className="text-xs font-semibold text-teal-800"
          >
            Xem tất cả →
          </Link>
        }
      >
        <div className="divide-y divide-slate-100">
          {drafts.data?.items.length ? (
            drafts.data.items.map((item) => (
              <div
                key={item.id}
                className="flex flex-wrap items-center justify-between gap-3 px-5 py-3 text-sm"
              >
                <div className="min-w-0">
                  <Link
                    href={"/my-questions/detail?id=" + item.id}
                    className="block max-w-lg truncate font-medium text-slate-900 hover:text-teal-800"
                  >
                    {item.title}
                  </Link>
                  <p className="text-xs text-slate-500">
                    {skillLabel[item.skill]} · {fmtDate(item.updated_at)} ·{" "}
                    {item.imported_count
                      ? "Đã nhập " + item.imported_count + " đề"
                      : "Chưa nhập ngân hàng"}
                  </p>
                </div>
                <button
                  className={secondaryClass}
                  disabled={busyId === item.id}
                  onClick={() => importDraft(item.id)}
                >
                  {busyId === item.id ? "Đang nhập..." : "Đưa vào ngân hàng"}
                </button>
              </div>
            ))
          ) : (
            <EmptyState
              title="Chưa có bản soạn"
              description="Tạo hoặc nhập đề; bản soạn sẽ hiện ở đây để đưa vào ngân hàng."
            />
          )}
        </div>
      </Section>
      <ConfirmDialog
        open={!!archive}
        onOpenChange={(open) => {
          if (!open) setArchive(null);
        }}
        title="Lưu trữ đề?"
        description="Đề sẽ rời ngân hàng đang xuất bản. Bài làm và lịch sử cũ được giữ lại."
        confirmLabel="Lưu trữ đề"
        onConfirm={archiveQuestion}
        busy={!!busyId}
        danger
      />
      <ConfirmDialog
        open={generateOpen}
        onOpenChange={setGenerateOpen}
        title="Sinh bản nháp bằng AI"
        description="Tác vụ này gọi OpenAI và phát sinh chi phí. Đề tạo xong chưa hiển thị cho người học cho đến khi được duyệt và xuất bản."
        confirmLabel="Sinh bản nháp"
        onConfirm={generateDraft}
        busy={busyId === "ai"}
      >
        <div className="mt-4 flex gap-2">
          <select
            aria-label="Kỹ năng"
            className={inputClass}
            value={aiSkill}
            onChange={(event) => {
              setAiSkill(event.target.value);
              setAiPart(1);
            }}
          >
            <option value="writing">Writing</option>
            <option value="speaking">Speaking</option>
            <option value="reading">Reading</option>
          </select>
          {aiSkill !== "reading" && (
            <select
              aria-label="Phần thi"
              className={inputClass}
              value={aiPart}
              onChange={(event) => setAiPart(Number(event.target.value))}
            >
              {Array.from(
                { length: aiSkill === "writing" ? 2 : 3 },
                (_, index) => (
                  <option key={index + 1} value={index + 1}>
                    {aiSkill === "writing" ? "Task " : "Part "}
                    {index + 1}
                  </option>
                ),
              )}
            </select>
          )}
        </div>
      </ConfirmDialog>
    </div>
  );
}

function Preview({ data }: { data: Detail }) {
  const content = data.content;
  const body =
    data.skill === "reading"
      ? String(content.content || "")
      : data.skill === "writing"
        ? String(content.instruction || "")
        : String(content.question_text || "");
  return (
    <article className="rounded-lg border border-slate-200 bg-white p-6">
      <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-teal-800">
        {skillLabel[data.skill]} ·{" "}
        {data.skill === "reading"
          ? "Bài đọc"
          : data.skill === "writing"
            ? "Task " + data.part
            : "Part " + data.part}
      </p>
      <h2 className="text-lg font-semibold text-slate-900">{data.title}</h2>
      <div
        lang="en"
        className="mt-5 whitespace-pre-wrap font-serif text-[17px] leading-8 text-slate-800"
      >
        {body}
      </div>
      {data.skill === "writing" && !!content.stimulus && (
        <blockquote
          lang="en"
          className="mt-5 whitespace-pre-wrap border-l-2 border-teal-700 bg-slate-50 p-4 font-serif text-base leading-7"
        >
          {String(content.stimulus)}
        </blockquote>
      )}
      {data.skill === "writing" && Array.isArray(content.requirements) && (
        <ul
          lang="en"
          className="mt-5 list-disc space-y-1 pl-5 font-serif text-sm"
        >
          {content.requirements.map((value, index) => (
            <li key={index}>{String(value)}</li>
          ))}
        </ul>
      )}
      {data.skill === "speaking" && !!content.situation && (
        <p
          lang="en"
          className="mt-5 rounded-md bg-slate-50 p-4 font-serif text-base leading-7"
        >
          {String(content.situation)}
        </p>
      )}
      {data.skill === "speaking" &&
        Array.isArray(content.topic_sets) &&
        content.topic_sets.map((set, index) => {
          const topic = set as { topic?: string; questions?: string[] };
          return (
            <section
              key={index}
              lang="en"
              className="mt-5 border-t border-slate-100 pt-4"
            >
              <h3 className="font-semibold">
                {topic.topic || "Topic " + (index + 1)}
              </h3>
              <ol className="mt-2 list-decimal space-y-2 pl-5 font-serif">
                {(topic.questions || []).map((question, questionIndex) => (
                  <li key={questionIndex}>{question}</li>
                ))}
              </ol>
            </section>
          );
        })}
      {data.skill === "speaking" &&
        Array.isArray(content.options) &&
        content.options.length > 0 && (
          <div lang="en" className="mt-5 grid gap-2 sm:grid-cols-2">
            {content.options.map((option, index) => (
              <p
                key={index}
                className="rounded-md border border-slate-200 p-3 font-serif"
              >
                {String.fromCharCode(65 + index)}. {String(option)}
              </p>
            ))}
          </div>
        )}
      {data.skill === "speaking" &&
        Array.isArray(content.suggested_ideas) &&
        content.suggested_ideas.length > 0 && (
          <div lang="en" className="mt-5">
            <h3 className="text-sm font-semibold">Ideas</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 font-serif">
              {content.suggested_ideas.map((idea, index) => (
                <li key={index}>{String(idea)}</li>
              ))}
            </ul>
          </div>
        )}
      {data.skill === "speaking" &&
        Array.isArray(content.follow_up_questions) &&
        content.follow_up_questions.length > 0 && (
          <div className="mt-5">
            <h3 className="text-sm font-semibold">Câu hỏi tiếp theo</h3>
            <ul lang="en" className="mt-2 list-disc space-y-2 pl-5 font-serif">
              {content.follow_up_questions.map((value, index) => (
                <li key={index}>{String(value)}</li>
              ))}
            </ul>
          </div>
        )}
      {data.skill === "reading" && (
        <div className="mt-6 space-y-5">
          {data.questions?.map((question) => (
            <div key={question.id} className="border-t pt-4">
              <p lang="en" className="font-medium">
                {question.question_number}. {question.question_text}
              </p>
              <div lang="en" className="mt-2 grid gap-1 text-sm sm:grid-cols-2">
                {Object.entries(question.options || {}).map(([key, value]) => (
                  <p key={key}>
                    {Array.isArray(question.options)
                      ? String.fromCharCode(65 + Number(key))
                      : key}
                    . {String(value)}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

export function QuestionDetailPanel({
  skill,
  id,
}: {
  skill: string;
  id: string;
}) {
  const { data, error, setError, loading, reload } = useAdminData<Detail>(
    "/admin/questions/" + skill + "/" + id,
  );
  return (
    <div>
      <PageHeader
        title={data?.title || "Chi tiết đề"}
        description="Duyệt nội dung và quyền hiển thị trước khi xuất bản."
        breadcrumb={
          <>
            <Link href="/admin/questions" className="hover:text-teal-800">
              Ngân hàng đề
            </Link>
            <span className="mx-2">/</span>
            {skillLabel[skill]}
          </>
        }
      />
      <ErrorState message={error} retry={reload} />
      {loading && !data ? (
        <div className="h-96 animate-pulse rounded-lg bg-slate-100" />
      ) : (
        data && (
          <Editor
            key={data.id}
            data={data}
            reload={reload}
            setError={setError}
          />
        )
      )}
    </div>
  );
}
function Editor({
  data,
  reload,
  setError,
}: {
  data: Detail;
  reload: () => void;
  setError: (message: string) => void;
}) {
  const router = useRouter();
  const [tier, setTier] = useState(data.access_tier),
    [trial, setTrial] = useState(data.available_for_free_trial),
    [featured, setFeatured] = useState(data.is_featured);
  const [topic, setTopic] = useState(data.topic),
    [title, setTitle] = useState(data.title),
    [body, setBody] = useState(
      String(data.content.instruction || data.content.question_text || ""),
    ),
    [stimulus, setStimulus] = useState(String(data.content.stimulus || ""));
  const [answers, setAnswers] = useState<Record<string, string>>(
    Object.fromEntries(
      (data.questions || []).map((question) => [
        question.id,
        question.correct_answer || "",
      ]),
    ),
  );
  const [preview, setPreview] = useState(false),
    [archive, setArchive] = useState(false),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const published = data.is_published && data.access_tier !== "INTERNAL";
  async function savePublication(isPublished: boolean) {
    setBusy(true);
    try {
      await api("/admin/questions/" + data.skill + "/" + data.id, {
        method: "PATCH",
        body: JSON.stringify({
          is_published: isPublished,
          access_tier: tier,
          available_for_free_trial: trial,
          is_featured: featured,
        }),
      });
      setNotice(isPublished ? "Đã xuất bản đề." : "Đã lưu bản nháp.");
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveContent() {
    setBusy(true);
    try {
      await api("/admin/questions/" + data.skill + "/" + data.id + "/content", {
        method: "PATCH",
        body: JSON.stringify({
          topic,
          ...(data.skill === "reading"
            ? { title }
            : data.skill === "writing"
              ? { instruction: body, stimulus }
              : { question_text: body }),
        }),
      });
      setNotice("Đã lưu nội dung.");
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveKey(keyId: string) {
    setBusy(true);
    try {
      await api("/admin/questions/reading/" + data.id + "/keys/" + keyId, {
        method: "PATCH",
        body: JSON.stringify({
          correct_answer: answers[keyId],
          answer_key_source: "admin_reviewed",
        }),
      });
      setNotice("Đã lưu đáp án.");
      reload();
    } catch (failure) {
      setError((failure as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function archiveQuestion() {
    setBusy(true);
    try {
      await api("/admin/questions/" + data.skill + "/" + data.id, {
        method: "DELETE",
      });
      router.push("/admin/questions");
    } catch (failure) {
      setError((failure as Error).message);
      setBusy(false);
    }
  }
  return (
    <div>
      <Notice text={notice} onClose={() => setNotice("")} />
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <StatusBadge status={status(data)} />
        <StatusBadge status={data.access_tier} />
        <span className="text-xs text-slate-500">
          {skillLabel[data.skill]} · {data.part} · {data.topic} ·{" "}
          {fmtNumber(data.attempts)} lượt luyện · {fmtDate(data.created_at)}
        </span>
      </div>
      <div className="mb-5 flex flex-wrap gap-2">
        <button
          className={preview ? secondaryClass : primaryClass}
          onClick={() => setPreview(false)}
        >
          Biên tập
        </button>
        <button
          className={preview ? primaryClass : secondaryClass}
          onClick={() => setPreview(true)}
        >
          Xem như người học
        </button>
      </div>
      {preview ? (
        <Preview
          data={{
            ...data,
            title,
            topic,
            content: {
              ...data.content,
              ...(data.skill === "reading"
                ? { title }
                : data.skill === "writing"
                  ? { instruction: body, stimulus }
                  : { question_text: body }),
            },
          }}
        />
      ) : (
        <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_310px]">
          <div className="space-y-5">
            <Section title="Nội dung đề">
              <div className="space-y-4 p-5">
                <label className="block text-xs font-medium text-slate-600">
                  Chủ đề
                  <input
                    className={inputClass + " mt-1 w-full"}
                    value={topic}
                    onChange={(event) => setTopic(event.target.value)}
                    disabled={published}
                  />
                </label>
                {data.skill === "reading" ? (
                  <label className="block text-xs font-medium text-slate-600">
                    Tiêu đề
                    <input
                      className={inputClass + " mt-1 w-full"}
                      value={title}
                      onChange={(event) => setTitle(event.target.value)}
                      disabled={published}
                    />
                  </label>
                ) : (
                  <label className="block text-xs font-medium text-slate-600">
                    {data.skill === "writing" ? "Yêu cầu bài viết" : "Câu hỏi"}
                    <textarea
                      className={inputClass + " mt-1 min-h-36 w-full py-2"}
                      value={body}
                      onChange={(event) => setBody(event.target.value)}
                      disabled={published}
                    />
                  </label>
                )}
                {data.skill === "writing" && (
                  <label className="block text-xs font-medium text-slate-600">
                    Dữ liệu / tình huống
                    <textarea
                      className={inputClass + " mt-1 min-h-28 w-full py-2"}
                      value={stimulus}
                      onChange={(event) => setStimulus(event.target.value)}
                      disabled={published}
                    />
                  </label>
                )}
                {published && (
                  <p className="text-xs text-amber-800">
                    Chuyển đề về bản nháp trước khi sửa nội dung. Bài làm cũ
                    được giữ lại.
                  </p>
                )}
                <button
                  className={secondaryClass}
                  disabled={published || busy}
                  onClick={saveContent}
                >
                  Lưu nội dung
                </button>
              </div>
            </Section>
            {data.skill === "reading" && (
              <Section title="Đáp án Reading">
                <div className="divide-y divide-slate-100 px-5">
                  {data.questions?.map((question) => (
                    <div
                      key={question.id}
                      className="flex flex-wrap items-center gap-3 py-3 text-sm"
                    >
                      <p className="min-w-48 flex-1">
                        {question.question_number}. {question.question_text}
                      </p>
                      <select
                        aria-label={"Đáp án câu " + question.question_number}
                        className={inputClass}
                        value={answers[question.id] || ""}
                        onChange={(event) =>
                          setAnswers({
                            ...answers,
                            [question.id]: event.target.value,
                          })
                        }
                        disabled={published}
                      >
                        <option value="">Chọn đáp án</option>
                        {["A", "B", "C", "D"].map((value) => (
                          <option key={value}>{value}</option>
                        ))}
                      </select>
                      <button
                        className={secondaryClass}
                        disabled={published || busy || !answers[question.id]}
                        onClick={() => saveKey(question.id)}
                      >
                        Lưu
                      </button>
                    </div>
                  ))}
                </div>
              </Section>
            )}
          </div>
          <div className="space-y-4">
            <Section title="Phân loại & quyền">
              <div className="space-y-4 p-5 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Kỹ năng</span>
                  <strong>{skillLabel[data.skill]}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Phần</span>
                  <strong>{data.part}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Nguồn</span>
                  <strong>{data.source}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Kiểm tra chất lượng</span>
                  <strong>{data.quality_valid ? "Đạt" : "Cần duyệt"}</strong>
                </div>
                <label className="block text-xs font-medium text-slate-600">
                  Tầng truy cập
                  <select
                    className={inputClass + " mt-1 w-full"}
                    value={tier}
                    onChange={(event) => {
                      setTier(event.target.value);
                      if (event.target.value !== "FREE_TRIAL") setTrial(false);
                    }}
                  >
                    <option value="VIP">VIP</option>
                    <option value="FREE_TRIAL">Trial</option>
                    <option value="INTERNAL">Nội bộ</option>
                  </select>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={trial}
                    onChange={(event) => {
                      setTrial(event.target.checked);
                      if (event.target.checked) setTier("FREE_TRIAL");
                    }}
                  />
                  Cho dùng trong trial
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={featured}
                    onChange={(event) => setFeatured(event.target.checked)}
                  />
                  Đề nổi bật
                </label>
                {trial && (
                  <p className="text-xs text-amber-800">
                    Pool trial chỉ hỗ trợ Writing Task 1 hoặc Speaking Part 1.
                  </p>
                )}
              </div>
            </Section>
            <Section title="Xuất bản">
              <div className="space-y-2 p-5">
                <button
                  className={primaryClass + " w-full"}
                  disabled={busy}
                  onClick={() => savePublication(true)}
                >
                  {published ? "Lưu thay đổi" : "Xuất bản đề"}
                </button>
                <button
                  className={secondaryClass + " w-full"}
                  disabled={busy}
                  onClick={() => savePublication(false)}
                >
                  Chuyển về bản nháp
                </button>
                <div className="border-t border-slate-100 pt-3">
                  <button
                    className={dangerClass + " w-full"}
                    onClick={() => setArchive(true)}
                  >
                    Lưu trữ đề
                  </button>
                </div>
              </div>
            </Section>
          </div>
        </div>
      )}
      <ConfirmDialog
        open={archive}
        onOpenChange={setArchive}
        title="Lưu trữ đề?"
        description="Đề sẽ không còn hiển thị cho người học. Các bài làm trước đây vẫn được giữ."
        confirmLabel="Lưu trữ đề"
        onConfirm={archiveQuestion}
        busy={busy}
        danger
      />
    </div>
  );
}
