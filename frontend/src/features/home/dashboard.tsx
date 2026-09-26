"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  PenLine,
  Mic,
  BookOpenText,
  Sparkles,
  Clock3,
  ChartNoAxesCombined,
} from "lucide-react";
import { useAuth } from "@/features/auth/auth-provider";
import { useLearning } from "@/features/learning/shared";
import { staticPageUrl } from "@/lib/static-page-url";
import { api } from "@/services/api";
import { score, cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { PageTitle, Caption, Body, Small, Metric } from "@/components/ui/typography";
import { FadeIn, StaggerContainer, StaggerItem, AnimatedNumber } from "@/components/ui/motion";
import { PracticeCards } from "@/features/writing/practice-cards";
import type { Progress } from "@/types";
import type { Overview, Today } from "@/features/learning/types";

const SKILLS = [
  {
    key: "WRITING",
    href: "/practice",
    icon: PenLine,
    title: "Writing",
    description: "Viết rõ ý, hiểu từng lỗi và hoàn thiện bài viết theo format VSTEP.",
  },
  {
    key: "SPEAKING",
    href: "/speaking",
    icon: Mic,
    title: "Speaking",
    description: "Nói tự nhiên, nghe lại bản ghi và cải thiện phát âm từng câu.",
  },
  {
    key: "READING",
    href: "/reading",
    icon: BookOpenText,
    title: "Reading",
    description: "Đọc hiểu 4 passage theo format thi với giải thích chi tiết.",
  },
] as const;

function greetingName(name: string | null | undefined, email: string) {
  return (name || email.split("@")[0]).split(" ")[0];
}

export function HomeDashboard() {
  const { user } = useAuth();
  const [progress, setProgress] = useState<Progress | null>(null);
  useEffect(() => {
    api<Progress>("/progress/summary")
      .then(setProgress)
      .catch(() => {});
  }, []);
  if (!user) return null;
  const isVip = user.access.tier === "VIP";
  const vipHours = user.access.vip_expires_at
    ? Math.max(0, Math.ceil((new Date(user.access.vip_expires_at).getTime() - Date.now()) / 3600000))
    : null;
  const hasHistory = (progress?.graded_attempts ?? 0) > 0;

  return (
    <div className="space-y-9">
      <FadeIn>
        <InsightBanner
          name={greetingName(user.name, user.email)}
          isVip={isVip}
          hasHistory={hasHistory}
          vipHours={vipHours}
          trialWriting={user.access.trial_remaining.WRITING_TASK1 ?? 0}
          trialSpeaking={user.access.trial_remaining.SPEAKING_PART1 ?? 0}
        />
      </FadeIn>

      {isVip && <TodayPlan />}

      <section>
        <div className="mb-5 flex items-end justify-between gap-4">
          <div>
            <Caption>Chọn nhịp luyện tập của bạn</Caption>
            <h2 className="mt-2 text-2xl font-bold tracking-tight">Bạn muốn luyện kỹ năng nào?</h2>
          </div>
          <Link
            href="/practice"
            className="hidden items-center gap-1 text-sm font-medium text-teal-800 sm:flex"
          >
            Khám phá
            <ArrowUpRight size={16} />
          </Link>
        </div>
        <StaggerContainer className="grid gap-5 md:grid-cols-3">
          {SKILLS.map((s) => (
            <StaggerItem key={s.key}>
              <SkillCard skill={s} progress={progress} />
            </StaggerItem>
          ))}
        </StaggerContainer>
      </section>

      <section>
        <Caption>Tiếp tục luyện Writing</Caption>
        <h2 className="mb-5 mt-2 text-xl font-bold tracking-tight">Chọn bài luyện tiếp theo</h2>
        <PracticeCards />
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <Card className="p-7">
          <div className="flex items-center justify-between">
            <h2 className="font-bold">Một vòng luyện tập, nhiều điều học được</h2>
            <Sparkles size={19} className="text-teal-600" />
          </div>
          <div className="mt-7 grid gap-6 sm:grid-cols-3">
            {[
              ["01", "Viết tập trung", "Đề rõ ràng, bộ đếm từ và tự động lưu bài."],
              ["02", "Hiểu bài viết", "Bốn tiêu chí cùng ưu tiên cải thiện rõ ràng."],
              ["03", "Tiến bộ từng ngày", "Chữa từng câu và theo dõi điểm qua các lần luyện."],
            ].map(([n, title, text]) => (
              <div key={n}>
                <span className="text-xs font-bold text-teal-700">{n} /</span>
                <h3 className="mb-2 mt-3 text-sm font-semibold">{title}</h3>
                <Small className="leading-6">{text}</Small>
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-7">
          <div className="flex items-center justify-between">
            <h2 className="font-bold">Hành trình của bạn</h2>
            <ChartNoAxesCombined size={19} className="text-teal-600" />
          </div>
          {hasHistory && progress ? (
            <>
              <div className="my-6 grid grid-cols-2 gap-4">
                <div>
                  <Metric size="md">
                    <AnimatedNumber value={progress.graded_attempts} decimals={0} />
                  </Metric>
                  <Small className="mt-2">Bài đã được chấm</Small>
                </div>
                <div>
                  <Metric size="md" className="text-teal-800">
                    {progress.average_task_score != null ? (
                      <AnimatedNumber value={progress.average_task_score} decimals={1} />
                    ) : (
                      "—"
                    )}
                  </Metric>
                  <Small className="mt-2">Điểm Task trung bình</Small>
                </div>
              </div>
              <Link href="/progress" className="flex items-center gap-2 text-sm font-semibold text-teal-800">
                Xem tiến độ
                <ArrowRight size={15} />
              </Link>
            </>
          ) : (
            <>
              <Body className="my-5 leading-7">
                Mỗi lần luyện đều đáng ghi nhận. Lưu bài viết và nhìn lại sự tiến bộ của chính mình.
              </Body>
              <Button asChild variant="outline" size="sm">
                <Link href="/progress">
                  Xem tiến độ
                  <ArrowRight />
                </Link>
              </Button>
            </>
          )}
        </Card>
      </section>
    </div>
  );
}

function InsightBanner({
  name,
  isVip,
  hasHistory,
  vipHours,
  trialWriting,
  trialSpeaking,
}: {
  name: string;
  isVip: boolean;
  hasHistory: boolean;
  vipHours: number | null;
  trialWriting: number;
  trialSpeaking: number;
}) {
  const [priorityNote, setPriorityNote] = useState<string | null>(null);
  const primaryHref = hasHistory ? "/history" : "/practice";
  const primaryLabel = hasHistory ? "Tiếp tục luyện tập" : "Bắt đầu luyện tập";

  return (
    <Card className="p-6 sm:p-7">
      {isVip && <PriorityNoteLoader onLoad={setPriorityNote} />}
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div className="max-w-xl">
          <Caption>Chào {name}</Caption>
          <h1 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
            {isVip ? "Hôm nay bạn muốn luyện gì?" : "Sẵn sàng cho buổi luyện hôm nay?"}
          </h1>
          <Body className="mt-3 leading-7">
            {priorityNote ||
              (isVip
                ? "Hoàn thành thêm bài luyện để nhận gợi ý ưu tiên học cá nhân hoá."
                : hasHistory
                  ? "Duy trì nhịp luyện đều đặn giúp bạn tiến bộ nhanh hơn qua từng tuần."
                  : "Luyện Writing, Speaking và Reading theo format VSTEP, nhận phản hồi chi tiết từ AI ngay sau khi nộp bài.")}
          </Body>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button asChild>
              <Link href={primaryHref}>
                {primaryLabel}
                <ArrowRight />
              </Link>
            </Button>
            {!isVip && (
              <Small className="flex items-center gap-1.5 text-stone-500">
                Trial còn lại: Writing {trialWriting} lượt · Speaking {trialSpeaking} lượt
              </Small>
            )}
          </div>
        </div>
        <Badge variant={isVip ? "premium" : "primary"} className="shrink-0">
          {isVip ? <Sparkles size={11} /> : null}
          {isVip ? "VIP" : "FREE"}
        </Badge>
      </div>
      {isVip && vipHours !== null && vipHours <= 48 && (
        <p className="mt-5 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
          VIP của bạn còn khoảng {Math.max(1, Math.ceil(vipHours / 24))} ngày.{" "}
          <Link className="font-semibold underline" href="/pricing">
            Gia hạn ngay
          </Link>
        </p>
      )}
      {!isVip && (
        <p className="mt-5 text-sm text-stone-500">
          <Link className="font-semibold text-teal-800" href="/pricing">
            Nâng cấp VIP
          </Link>{" "}
          để mở toàn bộ Writing, Speaking, Reading và phân tích học tập cá nhân.
        </p>
      )}
    </Card>
  );
}

function PriorityNoteLoader({ onLoad }: { onLoad: (note: string | null) => void }) {
  const { data } = useLearning<Overview>("/overview");
  useEffect(() => {
    if (data) onLoad(data.priority_note_vi || null);
  }, [data, onLoad]);
  return null;
}

function TodayPlan() {
  const { data } = useLearning<Today>("/today");
  if (!data) return null;
  const items = (data.items.length ? data.items : data.recommendations).slice(0, 3);
  if (!items.length) return null;
  return (
    <FadeIn delay={0.05}>
      <section>
        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <Caption>Học hôm nay</Caption>
            <h2 className="mt-2 text-xl font-bold tracking-tight">
              Khoảng {data.estimated_minutes} phút, từng bước nhỏ
            </h2>
          </div>
          <Link href="/learning/plan" className="hidden text-sm font-semibold text-teal-800 sm:block">
            Xem kế hoạch →
          </Link>
        </div>
        <StaggerContainer className="grid gap-3 sm:grid-cols-3">
          {items.map((item, i) => (
            <StaggerItem key={i}>
              <Link
                href={staticPageUrl(item.url)}
                className="panel panel-interactive flex h-full flex-col justify-between gap-4 p-5"
              >
                <div>
                  <span className="eyebrow">{item.skill}</span>
                  <p className="mt-2 text-sm font-semibold leading-6 text-stone-900">{item.title}</p>
                </div>
                <span className="flex items-center gap-1.5 text-xs text-stone-500">
                  <Clock3 size={13} />
                  {item.estimated_minutes} phút
                </span>
              </Link>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </section>
    </FadeIn>
  );
}

function SkillCard({
  skill,
  progress,
}: {
  skill: (typeof SKILLS)[number];
  progress: Progress | null;
}) {
  const Icon = skill.icon;
  const showScore = skill.key === "WRITING" && progress && progress.graded_attempts > 0;
  return (
    <Card interactive className="group flex h-full flex-col p-6">
      <div className="flex items-center justify-between">
        <span className="flex size-11 items-center justify-center rounded-xl bg-teal-50 text-teal-800 transition-transform duration-200 group-hover:-translate-y-0.5">
          <Icon size={22} />
        </span>
        {showScore && (
          <div className="text-right">
            <p className="text-xs text-stone-400">Điểm gần nhất</p>
            <p className="text-lg font-bold tabular-nums text-teal-800">
              {score(progress!.average_task_score)}
            </p>
          </div>
        )}
      </div>
      <h3 className="mt-4 text-xl font-bold">{skill.title}</h3>
      <Body className="mt-2 flex-1 leading-6">{skill.description}</Body>
      <div className="mt-5 flex items-center justify-between border-t border-stone-100 pt-4">
        <Link href={skill.href} className="text-sm font-semibold text-teal-800">
          Luyện {skill.title} →
        </Link>
        <ArrowRight
          size={16}
          className={cn(
            "text-stone-300 transition-transform duration-200",
            "group-hover:translate-x-1 group-hover:text-teal-700",
          )}
        />
      </div>
    </Card>
  );
}
