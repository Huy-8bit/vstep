"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/services/api";
import type { Attempt, Exam } from "@/types";

type Draft = { answer: string; revision: number; savedAt: number };
export const draftKey = (userId: string, attemptId: string) =>
  `vstep:draft:${userId}:${attemptId}`;

export function useAutosave(exam: Exam, userId: string) {
  const [initial] = useState(() => {
    const answers: Record<string, string> = {},
      conflicts: Record<string, boolean> = {};
    let restored = false;
    for (const attempt of exam.attempts) {
      answers[attempt.id] = attempt.answer;
      try {
        const raw = localStorage.getItem(draftKey(userId, attempt.id));
        const draft: Draft | null = raw ? JSON.parse(raw) : null;
        if (
          draft &&
          typeof draft.answer === "string" &&
          draft.answer !== attempt.answer
        ) {
          answers[attempt.id] = draft.answer;
          restored = true;
          conflicts[attempt.id] = draft.revision < attempt.revision;
        }
      } catch {
        /* Server copy remains usable if local storage is disabled. */
      }
    }
    return { answers, conflicts, restored };
  });
  const [answers, setAnswers] = useState(initial.answers);
  const [conflicts, setConflicts] = useState(initial.conflicts);
  const [status, setStatus] = useState(
    initial.restored ? "Đang lưu..." : "Đã lưu",
  );
  const [error, setError] = useState("");
  const [localWarning, setLocalWarning] = useState("");
  const values = useRef(initial.answers);
  const blocked = useRef(initial.conflicts);
  const saved = useRef(
    Object.fromEntries(exam.attempts.map((a) => [a.id, a.answer])),
  );
  const revisions = useRef(
    Object.fromEntries(exam.attempts.map((a) => [a.id, a.revision])),
  );
  const pending = useRef<Promise<void> | null>(null);
  const active = useRef(exam.status === "IN_PROGRESS");
  const persist = useCallback(
    (id: string, answer: string) => {
      try {
        localStorage.setItem(
          draftKey(userId, id),
          JSON.stringify({
            answer,
            revision: revisions.current[id],
            savedAt: Date.now(),
          }),
        );
      } catch {
        setLocalWarning(
          "Trình duyệt không cho lưu bản nháp trên thiết bị. Hãy giữ trang mở và kiểm tra trạng thái lưu máy chủ.",
        );
      }
    },
    [userId],
  );

  const flush = useCallback(async () => {
    if (pending.current) return pending.current;
    if (!active.current) return;
    const work = async () => {
      for (const id of Object.keys(values.current)) {
        if (blocked.current[id] || values.current[id] === saved.current[id])
          continue;
        const answer = values.current[id];
        setStatus("Đang lưu...");
        try {
          const result = await api<Attempt>(`/attempts/${id}`, {
            method: "PATCH",
            body: JSON.stringify({ answer, revision: revisions.current[id] }),
          });
          saved.current[id] = result.answer;
          revisions.current[id] = result.revision;
          persist(id, values.current[id]);
          setError("");
        } catch (e) {
          if (e instanceof ApiError && e.code === "revision_conflict") {
            blocked.current = { ...blocked.current, [id]: true };
            setConflicts(blocked.current);
          }
          if (e instanceof ApiError && e.code === "exam_closed")
            active.current = false;
          setStatus("Không thể kết nối");
          setError((e as Error).message);
          throw e;
        }
      }
      setStatus(
        Object.keys(values.current).some(
          (id) => values.current[id] !== saved.current[id],
        )
          ? "Đang lưu..."
          : "Đã lưu",
      );
    };
    pending.current = work().finally(() => {
      pending.current = null;
    });
    return pending.current;
  }, [persist]);

  const change = useCallback(
    (id: string, answer: string) => {
      values.current = { ...values.current, [id]: answer };
      setAnswers(values.current);
      persist(id, answer);
      setStatus("Đang lưu...");
    },
    [persist],
  );
  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void flush().catch(() => {});
    }, 1000);
    return () => clearTimeout(timeout);
  }, [answers, flush]);
  useEffect(() => {
    const retry = () => {
      void flush().catch(() => {});
    };
    const timer = window.setInterval(retry, 8000);
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (
        active.current &&
        Object.keys(values.current).some(
          (id) => values.current[id] !== saved.current[id],
        )
      )
        event.preventDefault();
    };
    window.addEventListener("online", retry);
    window.addEventListener("beforeunload", beforeUnload);
    return () => {
      clearInterval(timer);
      window.removeEventListener("online", retry);
      window.removeEventListener("beforeunload", beforeUnload);
    };
  }, [flush]);

  async function resolve(id: string, useLocal: boolean) {
    const latest = await api<Attempt>(`/attempts/${id}`);
    revisions.current[id] = latest.revision;
    saved.current[id] = latest.answer;
    blocked.current = { ...blocked.current, [id]: false };
    setConflicts(blocked.current);
    change(id, useLocal ? values.current[id] : latest.answer);
    setError("");
  }
  async function prepareSubmit() {
    // Let an already-running PATCH finish before taking the final revision snapshot.
    if (pending.current) await pending.current.catch(() => {});
    if (Object.values(blocked.current).some(Boolean))
      throw new Error("Hãy chọn bản nháp cần giữ trước khi nộp bài.");
    return Object.fromEntries(
      Object.entries(values.current).map(([id, answer]) => [
        id,
        { answer, revision: revisions.current[id] },
      ]),
    );
  }
  function complete(result: Exam) {
    active.current = false;
    for (const a of result.attempts) {
      if (a.answer === values.current[a.id]) {
        try {
          localStorage.removeItem(draftKey(userId, a.id));
        } catch {
          /* No local storage available. */
        }
      }
    }
  }
  return {
    answers,
    status,
    error,
    localWarning,
    conflicts,
    restored: initial.restored,
    change,
    flush,
    resolve,
    prepareSubmit,
    complete,
  };
}
