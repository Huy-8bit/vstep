"use client";
import { ErrorNotice } from "@/components/feedback";
import { Button } from "@/components/ui/button";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className="mx-auto max-w-lg py-16">
      <h1 className="text-2xl font-bold">Trang chưa tải được</h1>
      <ErrorNotice message="Đã có lỗi khi mở trang. Bản nháp đã lưu trên thiết bị vẫn được giữ lại." />
      <Button onClick={reset}>Thử lại</Button>
    </div>
  );
}
