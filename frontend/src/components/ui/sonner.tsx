"use client";
import { Toaster as Sonner } from "sonner";

export function Toaster() {
  return (
    <Sonner
      position="bottom-right"
      toastOptions={{
        classNames: {
          toast:
            "!rounded-xl !border !border-stone-200 !bg-white !shadow-lg !text-stone-900 !text-sm !font-medium",
          description: "!text-stone-500",
          actionButton: "!bg-teal-800 !text-white",
          success: "!border-emerald-200",
          error: "!border-red-200",
        },
      }}
    />
  );
}
