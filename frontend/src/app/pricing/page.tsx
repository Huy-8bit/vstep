"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Check, Sparkles, ArrowRight } from "lucide-react";
import { api, post } from "@/services/api";
import { useAuth } from "@/features/auth/auth-provider";
import { ErrorNotice } from "@/components/feedback";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Caption, PageTitle, Body, Metric, Small } from "@/components/ui/typography";
import { StaggerContainer, StaggerItem } from "@/components/ui/motion";
import { cn } from "@/lib/utils";

type Plan = {
  id: string;
  code: string;
  name: string;
  duration_days: number;
  price_vnd: number;
};

const VIP_BENEFITS = [
  "Writing Task 1 & 2 không giới hạn",
  "Speaking Part 1, 2, 3 không giới hạn",
  "Reading đầy đủ · phát âm · AI chấm chi tiết",
  "Từ vựng và phân tích học tập cá nhân",
];

export default function PricingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    api<{ items: Plan[] }>("/subscription/plans")
      .then((data) => setPlans(data.items))
      .catch((e) => setError(e.message));
    if (user) post("/events", { name: "PRICING_VIEWED" }).catch(() => {});
  }, [user]);
  async function choose(code: string) {
    if (!user) {
      router.push(`/login?next=${encodeURIComponent("/pricing")}`);
      return;
    }
    setBusy(code);
    setError("");
    try {
      await post("/payments", { plan_code: code });
      router.push("/account/subscription");
    } catch (e) {
      setError((e as Error).message);
      setBusy("");
    }
  }
  const recommended = Math.max(...plans.map((p) => p.duration_days), 0);

  return (
    <div className="space-y-8">
      <div>
        <Caption>Học theo nhịp của bạn</Caption>
        <PageTitle className="mt-2">Chọn quyền luyện tập</PageTitle>
        <Body className="mt-3 max-w-2xl leading-7">
          Bạn có thể thử Writing Task 1 và Speaking Part 1, mỗi kỹ năng một lần.
          VIP mở toàn bộ lộ trình luyện VSTEP.
        </Body>
      </div>
      {error && <ErrorNotice message={error} />}
      <StaggerContainer className="grid items-stretch gap-5 md:grid-cols-4">
        <StaggerItem>
          <Card className="flex h-full flex-col p-6">
            <Badge variant="neutral" className="w-fit">
              FREE
            </Badge>
            <Metric size="md" className="mt-4">
              0đ
            </Metric>
            <ul className="mt-5 flex-1 space-y-2.5 text-sm leading-6 text-stone-600">
              <li className="flex gap-2">
                <Check size={16} className="mt-0.5 shrink-0 text-teal-600" />1
                lần Writing Task 1
              </li>
              <li className="flex gap-2">
                <Check size={16} className="mt-0.5 shrink-0 text-teal-600" />1
                lần Speaking Part 1
              </li>
              <li className="flex gap-2">
                <Check size={16} className="mt-0.5 shrink-0 text-teal-600" />
                Có chấm và nhận phản hồi AI
              </li>
            </ul>
            <Link
              href={user ? "/practice/task-1" : "/register"}
              className="mt-6 flex items-center gap-1 text-sm font-semibold text-teal-800"
            >
              Bắt đầu miễn phí
              <ArrowRight size={15} />
            </Link>
          </Card>
        </StaggerItem>
        {plans.map((plan) => {
          const isRecommended = plan.duration_days === recommended;
          return (
            <StaggerItem key={plan.code}>
              <Card
                className={cn(
                  "flex h-full flex-col p-6",
                  isRecommended &&
                    "border-teal-300 bg-gradient-to-b from-teal-50/70 to-transparent shadow-md",
                )}
              >
                {isRecommended ? (
                  <Badge variant="premium" className="w-fit">
                    <Sparkles size={11} />
                    Tiết kiệm nhất
                  </Badge>
                ) : (
                  <Badge variant="neutral" className="w-fit">
                    {plan.name}
                  </Badge>
                )}
                <Metric size="md" className={cn("mt-4", isRecommended && "text-teal-900")}>
                  {new Intl.NumberFormat("vi-VN").format(plan.price_vnd)}đ
                </Metric>
                {isRecommended && <Small className="mt-1">{plan.name}</Small>}
                <ul className="mt-5 flex-1 space-y-2.5 text-sm leading-6 text-stone-600">
                  {VIP_BENEFITS.map((b) => (
                    <li key={b} className="flex gap-2">
                      <Check size={16} className="mt-0.5 shrink-0 text-teal-600" />
                      {b}
                    </li>
                  ))}
                </ul>
                <Button
                  className="mt-6 w-full"
                  variant={isRecommended ? "default" : "outline"}
                  disabled={!!busy}
                  onClick={() => choose(plan.code)}
                >
                  {busy === plan.code ? "Đang tạo yêu cầu…" : "Chọn gói VIP"}
                </Button>
              </Card>
            </StaggerItem>
          );
        })}
      </StaggerContainer>
      <Small>
        Hiện hỗ trợ xác nhận thanh toán thủ công. Quyền VIP bắt đầu sau khi
        quản trị viên xác nhận; việc chọn gói chưa tự trừ tiền.
      </Small>
    </div>
  );
}
