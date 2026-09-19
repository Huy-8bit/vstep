"use client";

import { useCallback, useEffect, useState } from "react";
import { RequireAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice, Loading } from "@/components/feedback";
import { api } from "@/services/api";

type Group = {
  category: string;
  operation: string;
  model: string;
  calls: number;
  estimated_cost_usd: number;
  unknown_cost_calls: number;
  input_tokens: number;
  cached_input_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  avg_latency_ms: number;
};
type Overview = {
  known_product_cost_usd: number;
  unknown_cost_calls: number;
  avg_writing_task_cost_usd: number | null;
  avg_user_cost_usd: number | null;
  evaluation_cost_usd: number;
  note_vi: string;
  groups: Group[];
  attempts: {
    attempt_id: string;
    known_cost_usd: number;
    calls: number;
    last_call: string;
  }[];
  routes: { operation: string; model: string; reasoning_effort: string }[];
};
type AttemptCosts = {
  known_total_usd: number;
  unknown_cost_calls: number;
  calls: {
    id: string;
    operation: string;
    model: string;
    reasoning_effort: string | null;
    input_tokens: number;
    cached_input_tokens: number;
    output_tokens: number;
    reasoning_tokens: number;
    estimated_cost_usd: number | null;
    status: string;
    latency_ms: number;
  }[];
};
const money = (v: number | null) =>
  v === null ? "Chưa có dữ liệu" : `$${Number(v).toFixed(4)}`;

export function AICostDashboard() {
  return (
    <RequireAuth>
      <Dashboard />
    </RequireAuth>
  );
}

function Dashboard() {
  const [days, setDays] = useState(1);
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const fetchOverview = useCallback(
    () => api<Overview>(`/internal/ai-costs?days=${days}`),
    [days],
  );
  const load = useCallback(async () => {
    try {
      setData(await fetchOverview());
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, [fetchOverview]);
  useEffect(() => {
    let active = true;
    fetchOverview()
      .then((next) => {
        if (active) {
          setData(next);
          setError("");
        }
      })
      .catch((e: Error) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [fetchOverview]);
  const categoryCost = (...categories: string[]) =>
    data?.groups
      .filter((g) => categories.includes(g.category))
      .reduce((sum, g) => sum + g.estimated_cost_usd, 0) ?? 0;
  return (
    <div className="space-y-7">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Quản trị nội bộ</p>
          <h1 className="mt-2 text-3xl font-bold">Chi phí AI</h1>
        </div>
        <div className="flex gap-2">
          <select
            aria-label="Khoảng thời gian"
            className="rounded-lg border p-2"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          >
            <option value={1}>Hôm nay</option>
            <option value={7}>7 ngày</option>
            <option value={30}>30 ngày</option>
          </select>
          <Button variant="outline" onClick={load}>
            Cập nhật
          </Button>
        </div>
      </div>
      {error && <ErrorNotice message={error} />}
      {!data && !error && <Loading />}
      {data && (
        <>
          <p className="text-sm leading-6 text-stone-600">{data.note_vi}</p>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Tổng sản phẩm đã đo", data.known_product_cost_usd],
              ["Writing / lượt chấm", data.avg_writing_task_cost_usd],
              ["Trung bình / người dùng", data.avg_user_cost_usd],
              ["Benchmark riêng", data.evaluation_cost_usd],
              ["Chấm Writing", categoryCost("writing_grading")],
              [
                "Speaking và audio",
                categoryCost("speaking", "audio", "transcription", "tts"),
              ],
              ["Tạo và kiểm tra đề", categoryCost("generation")],
              ["Learning Coach", categoryCost("learning")],
            ].map(([label, value]) => (
              <div key={String(label)} className="panel p-5">
                <p className="text-sm text-stone-500">{label}</p>
                <p className="mt-3 text-2xl font-semibold">
                  {money(value as number | null)}
                </p>
              </div>
            ))}
          </div>
          {data.unknown_cost_calls > 0 && (
            <p className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">
              {data.unknown_cost_calls} lượt chưa có đủ thông tin giá hoặc
              usage; tổng hiện tại chưa bao gồm các lượt này.
            </p>
          )}
          <section className="panel overflow-x-auto p-5">
            <h2 className="mb-4 text-lg font-semibold">Theo model và tác vụ</h2>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2">Nhóm / tác vụ</th>
                  <th>Model</th>
                  <th>Lượt</th>
                  <th>Input / cache / output</th>
                  <th>Reasoning</th>
                  <th>Chi phí đã đo</th>
                </tr>
              </thead>
              <tbody>
                {data.groups.map((g) => (
                  <tr
                    key={g.operation + g.model + g.category}
                    className="border-b border-stone-100"
                  >
                    <td className="p-2">
                      {g.category}
                      <br />
                      <span className="text-xs text-stone-500">
                        {g.operation}
                      </span>
                    </td>
                    <td>{g.model}</td>
                    <td>{g.calls}</td>
                    <td>
                      {g.input_tokens} / {g.cached_input_tokens} /{" "}
                      {g.output_tokens}
                    </td>
                    <td>{g.reasoning_tokens}</td>
                    <td>
                      {money(g.estimated_cost_usd)}
                      {g.unknown_cost_calls > 0 && (
                        <span className="block text-xs text-amber-700">
                          {g.unknown_cost_calls} lượt chưa rõ
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section>
            <h2 className="mb-4 text-lg font-semibold">
              Chi phí từng bài gần đây
            </h2>
            <div className="space-y-3">
              {data.attempts.length ? (
                data.attempts.map((a) => (
                  <Attempt key={a.attempt_id} item={a} />
                ))
              ) : (
                <p className="text-sm text-stone-500">
                  Chưa có lượt gọi được gắn với bài làm trong khoảng này.
                </p>
              )}
            </div>
          </section>
          <details className="panel p-5">
            <summary className="cursor-pointer font-semibold">
              Cấu hình model theo tác vụ
            </summary>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <tbody>
                  {data.routes.map((r) => (
                    <tr key={r.operation} className="border-b border-stone-100">
                      <td className="py-2">{r.operation}</td>
                      <td>{r.model}</td>
                      <td>{r.reasoning_effort}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}
    </div>
  );
}

function Attempt({ item }: { item: Overview["attempts"][number] }) {
  const [data, setData] = useState<AttemptCosts | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function inspect() {
    setBusy(true);
    try {
      setData(
        await api<AttemptCosts>(
          `/internal/ai-costs/attempts/${item.attempt_id}`,
        ),
      );
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="panel p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm">
          {item.attempt_id.slice(0, 8)} · {item.calls} lượt ·{" "}
          {money(item.known_cost_usd)}
        </p>
        <Button size="sm" variant="outline" disabled={busy} onClick={inspect}>
          {busy ? "Đang tải…" : "Xem từng lần gọi"}
        </Button>
      </div>
      {error && <ErrorNotice message={error} />}
      {data && (
        <div className="mt-4 overflow-x-auto">
          <p className="mb-3 text-sm">
            Tổng đã đo: {money(data.known_total_usd)}
            {data.unknown_cost_calls > 0 &&
              ` · ${data.unknown_cost_calls} lượt chưa đủ thông tin chi phí`}
          </p>
          <table className="w-full text-left text-xs">
            <thead>
              <tr>
                <th>Tác vụ</th>
                <th>Model / effort</th>
                <th>Input / cache / output</th>
                <th>Trạng thái</th>
                <th>USD</th>
              </tr>
            </thead>
            <tbody>
              {data.calls.map((c) => (
                <tr key={c.id} className="border-t">
                  <td className="py-3">{c.operation}</td>
                  <td>
                    {c.model} / {c.reasoning_effort || "—"}
                  </td>
                  <td>
                    {c.input_tokens} / {c.cached_input_tokens} /{" "}
                    {c.output_tokens}
                  </td>
                  <td>
                    {c.status} · {(c.latency_ms / 1000).toFixed(1)}s
                  </td>
                  <td>{money(c.estimated_cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
