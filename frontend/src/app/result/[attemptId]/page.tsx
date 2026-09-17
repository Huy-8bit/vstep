import { ResultView } from "@/features/grading/result-view";
export default async function ResultPage({
  params,
}: {
  params: Promise<{ attemptId: string }>;
}) {
  const { attemptId } = await params;
  return <ResultView id={attemptId} />;
}
