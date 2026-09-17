import { NextRequest } from "next/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  if (
    path[0] !== "v1" ||
    path.some((part) => part === ".." || part.includes("/"))
  )
    return Response.json({ detail: "Không tìm thấy API." }, { status: 404 });
  const headers = new Headers();
  for (const name of ["content-type", "cookie", "origin", "sec-fetch-site"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const body = ["GET", "HEAD"].includes(request.method)
    ? undefined
    : await request.text();
  if (body && new TextEncoder().encode(body).length > 100000)
    return Response.json({ detail: "Nội dung quá dài." }, { status: 413 });
  try {
    const response = await fetch(
      `${process.env.BACKEND_INTERNAL_URL || "http://localhost:8000"}/api/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
      {
        method: request.method,
        headers,
        body,
        cache: "no-store",
        signal: AbortSignal.timeout(330000),
        redirect: "manual",
      },
    );
    const outgoing = new Headers({
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    });
    for (const cookie of response.headers.getSetCookie())
      outgoing.append("Set-Cookie", cookie);
    if (response.headers.has("retry-after"))
      outgoing.set("Retry-After", response.headers.get("retry-after")!);
    return new Response(response.body, {
      status: response.status,
      headers: outgoing,
    });
  } catch {
    return Response.json(
      {
        detail: "Không thể kết nối backend. Vui lòng thử lại.",
        code: "backend_unavailable",
      },
      { status: 502 },
    );
  }
}
export { proxy as GET, proxy as POST, proxy as PATCH };
