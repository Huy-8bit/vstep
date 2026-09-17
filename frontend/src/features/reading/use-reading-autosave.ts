"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, post } from "@/services/api";
import type {
  Option,
  ReadingAnswer,
  ReadingResult,
  ReadingSession,
} from "./types";
export type Draft = {
  selected_answer: Option | null;
  is_marked_for_review: boolean;
  revision: number;
  time_spent_seconds: number;
  dirty: boolean;
  version: number;
};
export const draftKey = (user: string, session: string) =>
  `vstep-reading:${user}:${session}`;
const fromServer = (a: ReadingAnswer): Draft => ({
  selected_answer: a.selected_answer,
  is_marked_for_review: a.is_marked_for_review,
  revision: a.revision,
  time_spent_seconds: a.time_spent_seconds,
  dirty: false,
  version: 0,
});
const equal = (a: Draft, b: ReadingAnswer) =>
  a.selected_answer === b.selected_answer &&
  a.is_marked_for_review === b.is_marked_for_review;
export function useReadingAutosave(
  session: ReadingSession,
  userId: string,
  onClosed: () => void,
) {
  const key = draftKey(userId, session.id);
  const [initial] = useState(() => {
    let local: Record<string, Draft> = {};
    try {
      local = JSON.parse(localStorage.getItem(key) || "{}");
    } catch {
      /* Server values remain available. */
    }
    const values: Record<string, Draft> = {};
    const conflicts: Record<string, ReadingAnswer> = {};
    for (const a of session.answers) {
      const draft = local[a.question_id];
      values[a.question_id] = fromServer(a);
      if (
        draft?.dirty &&
        [null, "A", "B", "C", "D"].includes(draft.selected_answer) &&
        typeof draft.is_marked_for_review === "boolean" &&
        Number.isInteger(draft.revision)
      ) {
        values[a.question_id] = {
          ...draft,
          time_spent_seconds: Math.max(
            Number(draft.time_spent_seconds) || 0,
            a.time_spent_seconds,
          ),
          version: 0,
        };
        if (draft.revision !== a.revision && !equal(draft, a))
          conflicts[a.question_id] = a;
        else values[a.question_id].revision = a.revision;
      }
    }
    return { values, conflicts };
  });
  const ref = useRef(initial.values);
  const [values, setValues] = useState(initial.values);
  const [conflicts, setConflicts] = useState(initial.conflicts);
  const conflictRef = useRef(initial.conflicts);
  const [status, setStatus] = useState("Đã lưu");
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const active = useRef(true);
  const inFlight = useRef<Promise<void> | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flushRef = useRef<() => Promise<void>>(async () => {});
  const persist = useCallback(() => {
    try {
      localStorage.setItem(key, JSON.stringify(ref.current));
    } catch {
      setWarning(
        "Không lưu được bản dự phòng trên thiết bị. Giữ trang mở và kiểm tra trạng thái đồng bộ.",
      );
    }
  }, [key]);
  const publish = useCallback(() => {
    setValues({ ...ref.current });
    persist();
  }, [persist]);
  const changes = () =>
    Object.fromEntries(
      Object.entries(ref.current)
        .filter(([, d]) => d.dirty)
        .map(([id, d]) => [
          id,
          {
            selected_answer: d.selected_answer,
            is_marked_for_review: d.is_marked_for_review,
            revision: d.revision,
            time_spent_seconds: Math.floor(d.time_spent_seconds),
          },
        ]),
    );
  const flush = useCallback(async () => {
    if (inFlight.current) return await inFlight.current;
    if (!active.current || Object.keys(conflictRef.current).length) return;
    const snapshot = { ...ref.current };
    const body = Object.fromEntries(
      Object.entries(snapshot)
        .filter(([, d]) => d.dirty)
        .map(([id, d]) => [
          id,
          {
            selected_answer: d.selected_answer,
            is_marked_for_review: d.is_marked_for_review,
            revision: d.revision,
            time_spent_seconds: Math.floor(d.time_spent_seconds),
          },
        ]),
    );
    if (!Object.keys(body).length) return;
    inFlight.current = (async () => {
      setStatus("Đang lưu...");
      try {
        const response = await api<ReadingSession>(
          `/reading/sessions/${session.id}/answers`,
          { method: "PATCH", body: JSON.stringify({ answers: body }) },
        );
        if (response.status !== "IN_PROGRESS") {
          active.current = false;
          onClosed();
          return;
        }
        for (const a of response.answers) {
          const current = ref.current[a.question_id];
          if (!body[a.question_id]) continue;
          ref.current[a.question_id] =
            current.version === snapshot[a.question_id].version
              ? { ...fromServer(a), version: current.version }
              : {
                  ...current,
                  revision: a.revision,
                  time_spent_seconds: Math.max(
                    current.time_spent_seconds,
                    a.time_spent_seconds,
                  ),
                };
        }
        setError("");
        setStatus(
          Object.values(ref.current).some((d) => d.dirty)
            ? "Chờ lưu..."
            : "Đã lưu",
        );
        publish();
      } catch (e) {
        setStatus("Chưa đồng bộ");
        setError((e as Error).message);
        if (e instanceof ApiError && e.code === "revision_conflict") {
          try {
            const fresh = await api<ReadingSession>(
              `/reading/sessions/${session.id}`,
            );
            if (fresh.status !== "IN_PROGRESS") {
              active.current = false;
              onClosed();
              return;
            }
            const found: Record<string, ReadingAnswer> = {};
            for (const a of fresh.answers) {
              const draft = ref.current[a.question_id];
              if (
                draft.dirty &&
                draft.revision !== a.revision &&
                !equal(draft, a)
              )
                found[a.question_id] = a;
              else if (draft.dirty)
                ref.current[a.question_id] = { ...draft, revision: a.revision };
              else ref.current[a.question_id] = fromServer(a);
            }
            conflictRef.current = found;
            setConflicts(found);
            publish();
          } catch {
            /* Retry on the next online event without discarding local choices. */
          }
        }
      } finally {
        inFlight.current = null;
      }
    })();
    return await inFlight.current;
  }, [session.id, onClosed, publish]);
  useEffect(() => {
    flushRef.current = flush;
  }, [flush]);
  useEffect(() => {
    active.current = true;
    void flushRef.current();
    const retry = () => {
      void flushRef.current();
    };
    const timer = setInterval(retry, 5000);
    window.addEventListener("online", retry);
    const warn = (event: BeforeUnloadEvent) => {
      if (active.current && Object.values(ref.current).some((d) => d.dirty)) {
        persist();
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => {
      active.current = false;
      clearInterval(timer);
      if (saveTimer.current) clearTimeout(saveTimer.current);
      window.removeEventListener("online", retry);
      window.removeEventListener("beforeunload", warn);
    };
  }, [persist]);
  function change(
    id: string,
    change: Partial<Pick<Draft, "selected_answer" | "is_marked_for_review">>,
  ) {
    if (!active.current) return;
    ref.current[id] = {
      ...ref.current[id],
      ...change,
      dirty: true,
      version: ref.current[id].version + 1,
    };
    setStatus("Chờ lưu...");
    publish();
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      void flushRef.current();
    }, 400);
  }
  function tick(id: string) {
    if (!active.current || !ref.current[id]) return;
    const old = ref.current[id];
    ref.current[id] = {
      ...old,
      time_spent_seconds: old.time_spent_seconds + 1,
      dirty: true,
      version: old.version + 1,
    };
    persist();
  }
  function resolve(id: string, useLocal: boolean) {
    const server = conflictRef.current[id];
    ref.current[id] = useLocal
      ? {
          ...ref.current[id],
          revision: server.revision,
          dirty: true,
          version: ref.current[id].version + 1,
        }
      : fromServer(server);
    const rest = { ...conflictRef.current };
    delete rest[id];
    conflictRef.current = rest;
    setConflicts(rest);
    publish();
    if (!Object.keys(rest).length) void flushRef.current();
  }
  async function submit(expired = false) {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    active.current = false;
    try {
      if (inFlight.current) await inFlight.current;
      if (!expired && Object.keys(conflictRef.current).length)
        throw new Error(
          "Hãy giải quyết các đáp án khác nhau giữa hai tab trước khi nộp.",
        );
      const result = await post<ReadingResult>(
        `/reading/sessions/${session.id}/submit`,
        { answers: expired ? {} : changes() },
      );
      if (
        result.session.answers.every((a) =>
          equal(ref.current[a.question_id], a),
        )
      ) {
        try {
          localStorage.removeItem(key);
        } catch {
          /* Nonessential cleanup. */
        }
      }
      return result;
    } catch (e) {
      active.current = true;
      if (e instanceof ApiError && e.code === "revision_conflict")
        void flushRef.current();
      throw e;
    }
  }
  return {
    values,
    conflicts,
    status,
    error,
    warning,
    change,
    tick,
    resolve,
    flush,
    submit,
    hasPending: () => Object.values(ref.current).some((d) => d.dirty),
  };
}
