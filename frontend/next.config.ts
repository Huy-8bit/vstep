import type { NextConfig } from "next";
if (process.env.NODE_ENV === "production" && !process.env.NEXT_PUBLIC_API_BASE_URL) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is required for a production static build.");
}
const config: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  poweredByHeader: false,
};
export default config;
