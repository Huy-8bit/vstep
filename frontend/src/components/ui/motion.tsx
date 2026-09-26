"use client";
import {
  motion,
  useReducedMotion,
  useSpring,
  useTransform,
  AnimatePresence,
  type Variants,
} from "motion/react";
import { useEffect } from "react";

export { AnimatePresence };

const EASE = [0.16, 1, 0.3, 1] as const;

/** Fade + rise entrance for a single block. Use for section-level reveals. */
export function FadeIn({
  children,
  delay = 0,
  className,
  y = 10,
}: {
  children: React.ReactNode;
  delay?: number;
  className?: string;
  y?: number;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: reduce ? 0 : y }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduce ? 0.01 : 0.32, delay, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}

const staggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
};

const staggerItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: EASE } },
};

/** Wrap a list of StaggerItem children to reveal them in a gentle cascade. */
export function StaggerContainer({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      variants={reduce ? undefined : staggerContainer}
      initial={reduce ? undefined : "hidden"}
      animate={reduce ? undefined : "show"}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <motion.div className={className} variants={staggerItem}>
      {children}
    </motion.div>
  );
}

/** Counts up to `value` once on mount/change — for scores and dashboard metrics. */
export function AnimatedNumber({
  value,
  decimals = 1,
  className,
  suffix = "",
}: {
  value: number;
  decimals?: number;
  className?: string;
  suffix?: string;
}) {
  const reduce = useReducedMotion();
  const spring = useSpring(reduce ? value : 0, { stiffness: 90, damping: 20 });
  const display = useTransform(spring, (v) => `${v.toFixed(decimals)}${suffix}`);
  useEffect(() => {
    spring.set(value);
  }, [value, spring]);
  return (
    <motion.span className={className ? `tabular-nums ${className}` : "tabular-nums"}>
      {display}
    </motion.span>
  );
}

/** A progress ring that draws in once when its value is first known. */
export function AnimatedRing({
  value,
  size = 96,
  strokeWidth = 8,
  className,
  trackClassName = "text-stone-100",
  indicatorClassName = "text-teal-700",
}: {
  value: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  trackClassName?: string;
  indicatorClassName?: string;
}) {
  const reduce = useReducedMotion();
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, value));
  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      role="img"
      aria-label={`${pct}%`}
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        strokeWidth={strokeWidth}
        fill="none"
        className={trackClassName}
        stroke="currentColor"
      />
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        strokeWidth={strokeWidth}
        fill="none"
        stroke="currentColor"
        className={indicatorClassName}
        strokeLinecap="round"
        strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: circumference - (pct / 100) * circumference }}
        transition={{ duration: reduce ? 0.01 : 0.8, ease: EASE }}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
    </svg>
  );
}

/** Restrained checkmark draw for meaningful completion moments (not every action). */
export function SuccessCheck({ size = 40, className }: { size?: number; className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      className={className}
      initial={{ scale: reduce ? 1 : 0.85, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.25, ease: EASE }}
    >
      <circle cx="20" cy="20" r="19" className="stroke-emerald-500" strokeWidth="2" fill="none" />
      <motion.path
        d="M12 20.5l5.2 5.2L28.5 14.3"
        stroke="currentColor"
        className="text-emerald-500"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: reduce ? 0.01 : 0.35, delay: 0.15, ease: EASE }}
      />
    </motion.svg>
  );
}

/** Subtle page-level transition wrapper. Do not use for exam/focused screens. */
export function PageTransition({ children, className }: { children: React.ReactNode; className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: reduce ? 0 : 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: reduce ? 0.01 : 0.22, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}
