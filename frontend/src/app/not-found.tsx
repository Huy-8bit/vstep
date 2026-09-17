import Link from "next/link";
import { Button } from "@/components/ui/button";
export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <p className="eyebrow">404</p>
      <h1 className="my-4 text-3xl font-bold">Không tìm thấy trang</h1>
      <Button asChild>
        <Link href="/practice">Về trang luyện thi</Link>
      </Button>
    </div>
  );
}
