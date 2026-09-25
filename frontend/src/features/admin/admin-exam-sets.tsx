"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { post } from "@/services/api";
import {
  DataTable,
  EmptyState,
  ErrorState,
  FilterBar,
  Notice,
  PageHeader,
  Pagination,
  SearchInput,
  StatusBadge,
  cellClass,
  fmtDate,
  fmtNumber,
  inputClass,
  primaryClass,
  secondaryClass,
  useAdminData,
} from "./admin-ui";

type ExamSet = {
  id: string;
  title: string;
  skill: string;
  revision: number;
  bank_question_count: number;
  created_at: string;
};
type Imported = {
  items: { id: string; skill: string }[];
  already_imported: boolean;
};
const skillLabel: Record<string, string> = {
  writing: "Writing",
  speaking: "Speaking",
  reading: "Reading",
};

export function ExamSetsPanel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const page = Math.max(1, Number(searchParams.get("page") || 1));
  const skill = searchParams.get("skill") || "";
  const search = searchParams.get("search") || "";
  const [term, setTerm] = useState(search);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [actionError, setActionError] = useState("");
  const query = new URLSearchParams({
    offset: String((page - 1) * 20),
    limit: "20",
  });
  if (search) query.set("search", search);
  if (skill) query.set("skill", skill);
  const { data, error, loading, reload } = useAdminData<{
    items: ExamSet[];
    total: number;
  }>("/admin/exam-sets?" + query);
  function update(key: string, value: string) {
    const next = new URLSearchParams(searchParams.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== "page") next.delete("page");
    router.replace("/admin/exam-sets?" + next);
  }
  async function importSet(id: string) {
    setBusy(id);
    setActionError("");
    try {
      const result = await post<Imported>(
        "/admin/question-drafts/" + id + "/to-bank",
      );
      setNotice(
        result.already_imported
          ? "Bộ đề đã có trong ngân hàng."
          : "Đã đưa " +
              fmtNumber(result.items.length) +
              " phần vào ngân hàng dưới dạng nháp.",
      );
      reload();
    } catch (failure) {
      setActionError((failure as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <div>
      <PageHeader
        title="Bộ đề"
        description="Bộ đề đầy đủ đã soạn; đưa từng phần vào ngân hàng chung để kiểm duyệt và xuất bản."
        action={
          <Link className={primaryClass} href="/my-questions/new">
            Soạn bộ đề mới
          </Link>
        }
      />
      <Notice text={notice} onClose={() => setNotice("")} />
      <ErrorState message={actionError || error} retry={reload} />
      <FilterBar>
        <SearchInput
          value={term}
          onChange={setTerm}
          placeholder="Tìm tên bộ đề"
        />
        <button
          className={secondaryClass}
          onClick={() => update("search", term.trim())}
        >
          Tìm
        </button>
        <select
          aria-label="Kỹ năng"
          className={inputClass}
          value={skill}
          onChange={(event) => update("skill", event.target.value)}
        >
          <option value="">Mọi kỹ năng</option>
          <option value="writing">Writing</option>
          <option value="speaking">Speaking</option>
          <option value="reading">Reading</option>
        </select>
      </FilterBar>
      <DataTable
        headers={[
          "Bộ đề",
          "Kỹ năng",
          "Phiên bản",
          "Trong ngân hàng",
          "Ngày tạo",
          "Tác vụ",
        ]}
        loading={loading && !data}
        empty={
          !data?.items.length && (
            <EmptyState
              title="Chưa có bộ đề"
              description="Soạn một bộ đề đầy đủ để quản lý nội dung các phần thi cùng nhau."
              action={
                <Link className={primaryClass} href="/my-questions/new">
                  Soạn bộ đề
                </Link>
              }
            />
          )
        }
      >
        {data?.items.map((item) => (
          <tr key={item.id}>
            <td className={cellClass}>
              <Link
                href={"/my-questions/detail?id=" + item.id}
                className="font-medium text-teal-800 hover:underline"
              >
                {item.title}
              </Link>
            </td>
            <td className={cellClass}>
              {skillLabel[item.skill] || item.skill}
            </td>
            <td className={cellClass}>{item.revision}</td>
            <td className={cellClass}>
              <StatusBadge
                status={item.bank_question_count ? "IMPORTED" : "DRAFT"}
              />{" "}
              <span className="ml-1 text-xs text-slate-500">
                {item.bank_question_count} phần
              </span>
            </td>
            <td className={cellClass}>{fmtDate(item.created_at)}</td>
            <td className={cellClass}>
              <div className="flex items-center gap-2">
                <Link
                  className="text-sm font-medium text-teal-800"
                  href={"/my-questions/detail?id=" + item.id}
                >
                  Mở bản soạn
                </Link>
                <button
                  className={secondaryClass}
                  disabled={!!busy || !!item.bank_question_count}
                  onClick={() => importSet(item.id)}
                >
                  {busy === item.id ? "Đang đưa vào..." : "Đưa vào ngân hàng"}
                </button>
              </div>
            </td>
          </tr>
        ))}
      </DataTable>
      <Pagination
        page={page}
        pageSize={20}
        total={data?.total || 0}
        onPage={(value) => update("page", String(value))}
      />
    </div>
  );
}
