import Link from "next/link";
export function SkillSwitch({
  section,
  active,
}: {
  section: "history" | "progress";
  active: "writing" | "speaking";
}) {
  return (
    <nav
      aria-label="Chọn kỹ năng"
      className="mb-6 inline-flex gap-1 rounded-xl border border-stone-200 bg-white p-1"
    >
      {[
        ["writing", `/${section}`, "Writing"],
        ["speaking", `/speaking/${section}`, "Speaking"],
      ].map(([key, href, label]) => (
        <Link
          key={key}
          href={href}
          aria-current={active === key ? "page" : undefined}
          className={`rounded-lg px-6 py-2 text-sm font-semibold ${active === key ? "bg-teal-800 text-white" : "text-stone-500 hover:bg-stone-50"}`}
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
