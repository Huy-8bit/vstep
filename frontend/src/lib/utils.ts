import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
export const countWords = (text: string) =>
  (text.match(/[\p{L}\p{N}_]+(?:['’\-][\p{L}\p{N}_]+)*/gu) || []).length;
export const formatDate = (date: string) =>
  new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
export const score = (value: number | null | undefined) =>
  value == null ? "—" : value.toFixed(1);
export const DISCLAIMER =
  "Kết quả được AI ước tính nhằm phục vụ luyện tập và không phải điểm chính thức của kỳ thi VSTEP.";
