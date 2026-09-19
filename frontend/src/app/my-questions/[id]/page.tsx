import { LibraryDetail } from "@/features/library/library-detail";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <LibraryDetail id={id} />;
}
