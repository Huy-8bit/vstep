# VSTEP Practice Platform — UI Design System

A concise reference for the visual language introduced in the 2026 learner-UI redesign.
Source of truth for tokens: [`frontend/src/app/globals.css`](../frontend/src/app/globals.css).

## Principles

Modern, premium, calm, intelligent, motivating, fast, polished, smooth, focused.
Not: childish, cartoonish, gradient-heavy, glassy, bouncy, game-like, noisy.

## Colors

Two Tailwind palettes are **overridden at the token level** (not renamed), so every existing
`stone-*` / `teal-*` utility class across the codebase inherited the new look for free:

- `stone-*` → a cool, quiet ink-gray neutral (replaces the warm/brownish default), used for
  backgrounds, borders, and text.
- `teal-*` → a deeper, more confident "ink teal" (replaces the stock saturated teal), used as
  the single brand/primary accent.

Semantic CSS variables (for new components) live on `:root`:

```
--background --surface --surface-elevated --surface-hover --surface-sunken
--text-primary --text-secondary --text-muted --text-on-primary
--border --border-strong
--primary --primary-hover --primary-soft --primary-soft-strong
--success --success-soft --warning --warning-soft --danger --danger-soft --info --info-soft
```

Semantic accents (amber = warning/VIP, red = danger, emerald = success) are used sparingly and
never as a decorative rainbow. Gradients are reserved for: the logged-out hero, the score-reveal
card, and premium/VIP CTAs — never as a page background.

**Dark mode:** full dark values for both palettes and the semantic tokens are already defined
under `.dark` (see globals.css), and `@custom-variant dark` is wired for Tailwind's `dark:`
variant. It is **not yet exposed to users** — roughly 20% of existing components still use literal
`bg-white`/`text-white`/one-off `amber-*`/`red-*` classes that aren't dark-safe, and flipping the
toggle on globally today would make those specific screens unreadable. Follow-up: audit and
convert those files, then wire `next-themes` (already installed) into `layout.tsx` with a toggle.

## Typography

`Plus Jakarta Sans` (via `next/font/google`) for all UI text; `Georgia` serif stays for long-form
reading/writing content (`prose-writing`, `exam-editor`) to visually separate "reading mode" from
"interface chrome." Use the components in `components/ui/typography.tsx` instead of ad-hoc
`text-xl`/`text-2xl`:

`Display` · `PageTitle` · `SectionTitle` · `Lead` · `Body` · `Small` · `Caption` · `Label` · `Metric`

`Metric` is the deliberate treatment for headline numbers (scores, band levels, percentages) —
bold, tabular-nums, tight tracking, three sizes (`md`/`lg`/`xl`).

## Elevation, radius, borders

- Shadows are layered/soft, not the flat Tailwind defaults — `--shadow-xs/sm/md/lg/xl` are
  overridden globally, so plain `shadow-sm`/`shadow-lg` utilities already look premium.
- Base radius `--radius: 0.75rem` (unchanged — the app already converged on `rounded-xl`/`2xl`
  fairly consistently; we didn't fight that).
- `.panel` (39 files) / `.field` (22 files) / `.eyebrow` (33 files) are the pre-existing utility
  classes upgraded in place in `globals.css` — the single highest-leverage change in this pass,
  since it improved the majority of existing cards/inputs/labels without touching each file.
- `.panel-interactive` is an opt-in modifier for clickable cards: border brightens, shadow lifts,
  `translateY(-2px)` on hover.

## Motion

Presets (`--duration-micro/ui/section`, `--ease-out-premium`): 140ms / 200ms / 320ms, cubic-bezier
`(0.16, 1, 0.3, 1)`. The Tailwind **default** transition duration/easing is also overridden
globally, so existing `transition-colors` etc. calls got smoother for free.

Reusable primitives in `components/ui/motion.tsx` (built on the `motion` package):

- `FadeIn`, `StaggerContainer` / `StaggerItem` — section and card-grid entrances.
- `AnimatedNumber` — spring count-up, for scores and dashboard metrics only (not every render).
- `AnimatedRing`, `SuccessCheck`, `PageTransition`.
- All respect `prefers-reduced-motion` via `useReducedMotion()`; global CSS also collapses
  `animation`/`transition` durations under that media query as a floor.

`components/ui/ai-progress.tsx` (`AiProgressOverlay`) is the staged-loading pattern for AI grading
(Writing submit → exam-workspace.tsx). Stages are a general sense-of-progress on a timer, not tied
to real backend milestones — do not add fake percentages.

## Components

New primitives added under `components/ui/`: `card`, `badge`, `input`, `textarea`, `skeleton`,
`progress`, `separator`, `avatar`, `tooltip`, `dropdown-menu`, `sonner` (toasts), `ai-progress`,
`typography`, `motion`. `button`, `dialog`, `tabs` were pre-existing and got restyled in place
(`dialog`: fade+scale open/close; `tabs`: animated underline indicator instead of filled pills —
scales better with 6–7 tabs on result pages).

## Layout & navigation

- App shell (`components/shell.tsx`): desktop top nav collapsed from 10 items to 6 by grouping
  Writing/Speaking/Reading under one "Luyện tập" entry (the `/practice` hub now fans out to all
  three skills — see below). Account/tier live in a dropdown on the right.
- Mobile: a fixed bottom tab bar (Trang chủ / Luyện tập / Học tập / Lịch sử / Tài khoản) replaces
  cramped horizontal scrolling nav; the desktop nav is hidden below `md`.
- `/practice` is now a real multi-skill hub (Writing/Speaking/Reading entry cards with VIP badges
  on locked options) as well as Writing's own task picker — this was also the fix for a nav
  regression where consolidating the top nav would otherwise have made `/speaking` and `/reading`
  unreachable from primary navigation.

## Known gaps / good next steps

- Full success-state visual QA of the Writing result page's score header could not be completed
  live in this session — the local `.env` `OPENAI_API_KEY` is expired (`expired_secret_key` from
  OpenAI), so grading calls 502. The change was applied conservatively (styling/entrance-animation
  only, no data-flow changes) and passes typecheck; verify visually once a valid key is in place.
- Speaking/Reading practice & result pages, Vocabulary, Learning Analysis deep redesign, Auth
  pages, and Admin visual consistency are not yet covered by this pass — see the conversation
  summary for the full priority list.
