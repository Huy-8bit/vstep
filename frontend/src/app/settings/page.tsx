"use client";
import { useEffect, useState } from "react";
import { RequireAuth, useAuth } from "@/features/auth/auth-provider";
import { Button } from "@/components/ui/button";
import { ErrorNotice } from "@/components/feedback";
import { api } from "@/services/api";
export default function Page() {
  return (
    <RequireAuth>
      <Settings />
    </RequireAuth>
  );
}
function Settings() {
  const { user } = useAuth();
  const [rate, setRate] = useState("0.95");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [config, setConfig] = useState<{
    ai_configured: boolean;
    audio_analysis_configured: boolean;
    tts_configured: boolean;
  } | null>(null);
  useEffect(() => {
    try {
      setRate(localStorage.getItem("vstep-speaking-voice-rate") || "0.95");
    } catch {
      /* Defaults work without local storage. */
    }
    api<typeof config>("/speaking/config")
      .then(setConfig)
      .catch((e) => setError(e.message));
  }, []);
  async function microphone() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (!navigator.mediaDevices?.getUserMedia)
        throw new Error(
          "Ghi âm cần trình duyệt hỗ trợ và kết nối HTTPS hoặc localhost.",
        );
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const label = stream.getAudioTracks()[0]?.label || "Microphone";
      stream.getTracks().forEach((track) => track.stop());
      setMessage(`${label} đã sẵn sàng.`);
    } catch {
      setError(
        "Chưa truy cập được microphone. Cho phép Microphone ở biểu tượng ổ khóa cạnh địa chỉ trang; kiểm tra thêm quyền của trình duyệt trong cài đặt thiết bị.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="eyebrow">Không gian của bạn</p>
        <h1 className="mt-2 text-3xl font-bold">Cài đặt</h1>
      </div>
      <section className="panel p-6">
        <h2 className="font-bold">Tài khoản</h2>
        <p className="mt-3 text-sm text-stone-500">{user?.email}</p>
      </section>
      <section className="panel space-y-5 p-6">
        <h2 className="font-bold">Luyện Speaking</h2>
        <label className="block text-sm font-medium">
          Tốc độ giọng đọc trình duyệt
          <select
            className="field mt-2 max-w-xs"
            value={rate}
            onChange={(e) => {
              setRate(e.target.value);
              try {
                localStorage.setItem(
                  "vstep-speaking-voice-rate",
                  e.target.value,
                );
                setMessage("Đã lưu tốc độ đọc trên trình duyệt này.");
              } catch {
                setError("Không lưu được lựa chọn vào trình duyệt.");
              }
            }}
          >
            <option value="0.8">Chậm · 0.8×</option>
            <option value="0.95">Vừa phải · 0.95×</option>
            <option value="1.1">Nhanh · 1.1×</option>
          </select>
        </label>
        <p className="text-xs leading-6 text-stone-500">
          Áp dụng khi câu hỏi được đọc bằng giọng có sẵn của trình duyệt.
        </p>
        <Button variant="outline" disabled={busy} onClick={microphone}>
          {busy ? "Đang mở microphone..." : "Kiểm tra quyền microphone"}
        </Button>
        {message && (
          <p className="text-sm text-teal-700" role="status">
            {message}
          </p>
        )}
        {error && <ErrorNotice message={error} />}
      </section>
      <section className="panel p-6">
        <h2 className="mb-4 font-bold">Tính năng đang sẵn sàng</h2>
        <div className="space-y-3 text-sm">
          {[
            ["Đề mẫu và ghi âm", true],
            ["Chuyển lời nói & phản hồi ngôn ngữ AI", config?.ai_configured],
            [
              "Phân tích audio AI",
              config
                ? config.ai_configured && config.audio_analysis_configured
                : undefined,
            ],
            ["Giọng đọc AI", config?.tts_configured],
          ].map(([label, enabled]) => (
            <div key={String(label)} className="flex justify-between gap-4">
              <span>{label}</span>
              <span className={enabled ? "text-teal-700" : "text-stone-400"}>
                {enabled === undefined
                  ? "Đang tải..."
                  : enabled
                    ? "Sẵn sàng"
                    : "Chưa cấu hình"}
              </span>
            </div>
          ))}
        </div>
        <p className="mt-5 text-xs leading-6 text-stone-500">
          Nếu giọng đọc AI chưa sẵn sàng, hệ thống dùng giọng đọc của trình
          duyệt.
        </p>
      </section>
    </div>
  );
}
