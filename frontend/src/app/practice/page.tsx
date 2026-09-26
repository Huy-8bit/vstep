"use client";
import Link from "next/link";
import { PenLine, Mic, BookOpenText } from "lucide-react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { PracticeCards } from "@/features/writing/practice-cards";
import { FullTestStart } from "@/features/writing/practice-setup";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Caption, PageTitle, Body, SectionTitle } from "@/components/ui/typography";
import { StaggerContainer, StaggerItem } from "@/components/ui/motion";

const HUB = [
  {
    key: "WRITING",
    icon: PenLine,
    title: "Writing",
    description: "Thư/email và bài luận theo format VSTEP.",
    links: [
      { label: "Thi thử", href: "/practice#full-test", vip: true },
      { label: "Task 1", href: "/practice/task-1" },
      { label: "Task 2", href: "/practice/task-2", vip: true },
    ],
  },
  {
    key: "SPEAKING",
    icon: Mic,
    title: "Speaking",
    description: "Ba phần thi và luyện nhanh mỗi ngày.",
    links: [
      { label: "Thi thử", href: "/speaking", vip: true },
      { label: "Part 1", href: "/speaking?mode=PART1" },
      { label: "Part 2", href: "/speaking?mode=PART2", vip: true },
      { label: "Part 3", href: "/speaking?mode=PART3", vip: true },
    ],
  },
  {
    key: "READING",
    icon: BookOpenText,
    title: "Reading",
    description: "4 passage, 40 câu theo format thi thật.",
    links: [
      { label: "Thi thử", href: "/reading", vip: true },
      { label: "Luyện passage", href: "/reading?mode=PASSAGE_PRACTICE", vip: true },
      { label: "Theo dạng câu", href: "/reading?mode=QUESTION_TYPE_PRACTICE", vip: true },
    ],
  },
] as const;

function SkillHubCard({ skill, isVip }: { skill: (typeof HUB)[number]; isVip: boolean }) {
  const Icon = skill.icon;
  return (
    <Card className="flex flex-col p-6">
      <span className="mb-4 flex size-11 items-center justify-center rounded-xl bg-teal-50 text-teal-800">
        <Icon size={22} />
      </span>
      <h3 className="text-xl font-bold">{skill.title}</h3>
      <Body className="mt-2 leading-6">{skill.description}</Body>
      <div className="mt-5 flex flex-wrap gap-x-4 gap-y-2 border-t border-stone-100 pt-4 text-sm font-semibold text-teal-800">
        {skill.links.map((l) => (
          <Link key={l.href} href={l.href} className="inline-flex items-center gap-1.5">
            {l.label}
            {"vip" in l && l.vip && !isVip && (
              <Badge variant="premium" className="px-1.5 py-0.5 text-[9px]">
                VIP
              </Badge>
            )}
          </Link>
        ))}
      </div>
    </Card>
  );
}

export default function Practice() {
  const { user } = useAuth();
  const isVip = user?.role === "ADMIN" || user?.access?.tier === "VIP";
  return (
    <RequireAuth>
      <div className="space-y-10">
        <div>
          <Caption>Không gian luyện tập</Caption>
          <PageTitle className="mb-3 mt-2">Chọn kỹ năng và hình thức luyện</PageTitle>
          <Body>Bắt đầu với thi thử đầy đủ hoặc luyện có mục tiêu theo từng phần.</Body>
        </div>
        <StaggerContainer className="grid gap-5 md:grid-cols-3">
          {HUB.map((s) => (
            <StaggerItem key={s.key}>
              <SkillHubCard skill={s} isVip={isVip} />
            </StaggerItem>
          ))}
        </StaggerContainer>
        <div>
          <SectionTitle className="mb-5">Luyện Writing theo Task</SectionTitle>
          <PracticeCards />
          <FullTestStart />
        </div>
      </div>
    </RequireAuth>
  );
}
