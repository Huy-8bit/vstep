import Link from "next/link";
import { ArrowRight, Clock3, FileText, Mail, NotebookPen } from "lucide-react";
import { cn } from "@/lib/utils";
const choices = [
  {
    href: "/practice#full-test",
    eyebrow: "Trọn bộ bài thi",
    title: "Thi thử Writing",
    description:
      "Rèn nhịp làm bài với cả hai Task trong một phiên thi hoàn chỉnh.",
    detail: "60 phút · 2 bài viết",
    Icon: NotebookPen,
    featured: true,
  },
  {
    href: "/practice/task-1",
    eyebrow: "Task 1",
    title: "Viết thư & email",
    description:
      "Luyện cách truyền đạt thông tin với mục đích và văn phong phù hợp.",
    detail: "Tối thiểu 120 từ · Trọng số ⅓",
    Icon: Mail,
    featured: false,
  },
  {
    href: "/practice/task-2",
    eyebrow: "Task 2",
    title: "Viết bài luận",
    description:
      "Phát triển quan điểm, sắp xếp lập luận và diễn đạt ý tưởng rõ ràng.",
    detail: "Tối thiểu 250 từ · Trọng số ⅔",
    Icon: FileText,
    featured: false,
  },
];
export function PracticeCards() {
  return (
    <div className="grid gap-5 md:grid-cols-3">
      {choices.map(({ Icon, ...item }) => (
        <Link
          key={item.href}
          href={item.href}
          className={cn(
            "group flex flex-col rounded-2xl border p-6 transition-colors sm:p-7",
            item.featured
              ? "border-teal-800 bg-teal-800 text-white hover:bg-teal-900"
              : "border-stone-200 bg-white hover:border-teal-300",
          )}
        >
          <div className="mb-7 flex items-center justify-between">
            <span
              className={cn(
                "flex size-11 items-center justify-center rounded-xl",
                item.featured ? "bg-white/10" : "bg-stone-100 text-teal-800",
              )}
            >
              <Icon size={22} />
            </span>
            <span
              className={cn(
                "text-[10px] font-semibold uppercase tracking-widest",
                item.featured ? "text-teal-200" : "text-stone-400",
              )}
            >
              {item.eyebrow}
            </span>
          </div>
          <h3 className="text-xl font-bold">{item.title}</h3>
          <p
            className={cn(
              "mb-6 mt-3 flex-1 text-sm leading-6",
              item.featured ? "text-teal-100/80" : "text-stone-500",
            )}
          >
            {item.description}
          </p>
          <div
            className={cn(
              "flex items-center justify-between border-t pt-5 text-xs",
              item.featured
                ? "border-white/15 text-teal-100"
                : "border-stone-100 text-stone-500",
            )}
          >
            <span className="flex items-center gap-2">
              <Clock3 size={13} />
              {item.detail}
            </span>
            <ArrowRight size={17} />
          </div>
        </Link>
      ))}
    </div>
  );
}
