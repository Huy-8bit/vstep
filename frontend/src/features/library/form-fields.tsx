import type { ReactNode } from "react";
export function Field({
  label,
  value,
  onChange,
  multiline = false,
  hint,
  rows = 4,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
  hint?: string;
  rows?: number;
  type?: string;
}) {
  return (
    <label className="block space-y-1.5 text-sm">
      <span className="font-medium">{label}</span>
      {multiline ? (
        <textarea
          className="field min-h-24 w-full whitespace-pre-wrap"
          rows={rows}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          className="field w-full"
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      )}{" "}
      {hint && <span className="block text-xs text-stone-500">{hint}</span>}
    </label>
  );
}
export function Lines({
  label,
  values,
  onChange,
  hint,
}: {
  label: string;
  values: string[];
  onChange: (values: string[]) => void;
  hint?: string;
}) {
  return (
    <Field
      label={label}
      value={values.join("\n")}
      multiline
      onChange={(v) => onChange(v === "" ? [] : v.split("\n"))}
      hint={
        hint || "Mỗi mục trên một dòng. Giữ nguyên cách diễn đạt của đề gốc."
      }
    />
  );
}
export function SelectField({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  children: ReactNode;
}) {
  return (
    <label className="block space-y-1.5 text-sm">
      <span className="font-medium">{label}</span>
      <select
        className="field w-full"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {children}
      </select>
    </label>
  );
}
