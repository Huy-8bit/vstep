import { WeaknessDetail } from "@/features/learning/detail";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <WeaknessDetail id={id} />;
}
