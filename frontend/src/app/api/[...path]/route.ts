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
  for (const name of [
    "content-type",
    "cookie",
    "origin",
    "sec-fetch-site",
    "range",
    "if-range",
  ]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const audioUpload =
    path[1] === "speaking" &&
    ((path[2] === "answers" && path[4] === "audio") ||
      (path[2] === "pronunciation" &&
        path[3] === "practices" &&
        path[5] === "audio"));
  const library = path[1] === "my-questions";
  const limit = audioUpload
    ? 25 * 1024 * 1024
    : library && path[2] === "assets"
      ? 21 * 1024 * 1024
      : library
        ? 2 * 1024 * 1024
        : 100000;
  if (Number(request.headers.get("content-length") || 0) > limit)
    return Response.json(
      { detail: "Bản ghi vượt giới hạn tải lên." },
      { status: 413 },
    );
  let body: Uint8Array | undefined;
  if (!["GET", "HEAD"].includes(request.method) && request.body) {
    const reader = request.body.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) {
        await reader.cancel();
        return Response.json({ detail: "Nội dung quá dài." }, { status: 413 });
      }
      chunks.push(value);
    }
    body = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      body.set(chunk, offset);
      offset += chunk.length;
    }
  }
  try {
    const response = await fetch(
      `${process.env.BACKEND_INTERNAL_URL || "http://localhost:8000"}/api/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
      {
        method: request.method,
        headers,
        body: body as BodyInit | undefined,
        cache: "no-store",
        signal: AbortSignal.timeout(660000),
        redirect: "manual",
      },
    );
    const outgoing = new Headers({
      "Content-Type":
        response.headers.get("content-type") || "application/octet-stream",
      "Cache-Control": "no-store",
    });
    for (const name of [
      "content-range",
      "accept-ranges",
      "content-length",
      "content-disposition",
    ])
      if (response.headers.has(name))
        outgoing.set(name, response.headers.get(name)!);
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
export { proxy as GET, proxy as POST, proxy as PATCH, proxy as PUT };

export const DELETE = proxy;
