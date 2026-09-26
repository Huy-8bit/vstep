import { cn } from "@/lib/utils";

/**
 * Reusable typographic scale — use these instead of ad-hoc text-xl/text-2xl.
 * Display > PageTitle > SectionTitle > CardTitle > Body > Small > Caption > Metric > Label
 */

export function Display({ className, ...props }: React.ComponentProps<"h1">) {
  return (
    <h1
      className={cn(
        "text-4xl font-extrabold leading-[1.1] tracking-tight text-(--text-primary) sm:text-5xl",
        className,
      )}
      {...props}
    />
  );
}

export function PageTitle({ className, ...props }: React.ComponentProps<"h1">) {
  return (
    <h1
      className={cn(
        "text-2xl font-bold leading-tight tracking-tight text-(--text-primary) sm:text-3xl",
        className,
      )}
      {...props}
    />
  );
}

export function SectionTitle({ className, ...props }: React.ComponentProps<"h2">) {
  return (
    <h2
      className={cn(
        "text-lg font-bold leading-tight tracking-tight text-(--text-primary) sm:text-xl",
        className,
      )}
      {...props}
    />
  );
}

export function Lead({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p
      className={cn("text-base leading-7 text-(--text-secondary)", className)}
      {...props}
    />
  );
}

export function Body({ className, ...props }: React.ComponentProps<"p">) {
  return (
    <p className={cn("text-sm leading-6 text-(--text-secondary)", className)} {...props} />
  );
}

export function Small({ className, ...props }: React.ComponentProps<"p">) {
  return <p className={cn("text-xs leading-5 text-(--text-muted)", className)} {...props} />;
}

export function Caption({ className, ...props }: React.ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "text-[11px] font-bold uppercase tracking-[0.12em] text-(--primary)",
        className,
      )}
      {...props}
    />
  );
}

export function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label
      className={cn("text-sm font-semibold text-(--text-primary)", className)}
      {...props}
    />
  );
}

/** Deliberate treatment for headline metrics (scores, band levels, percentages). */
export function Metric({
  className,
  size = "lg",
  ...props
}: React.ComponentProps<"span"> & { size?: "md" | "lg" | "xl" }) {
  return (
    <span
      className={cn(
        "font-extrabold tabular-nums tracking-tight text-(--text-primary)",
        size === "md" && "text-3xl",
        size === "lg" && "text-5xl",
        size === "xl" && "text-6xl",
        className,
      )}
      {...props}
    />
  );
}
