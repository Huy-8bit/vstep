export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code = "",
    public details: Record<string, unknown> = {},
  ) {
    super(message);
  }
}
let refreshPromise: Promise<boolean> | null = null;

export async function api<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
  binary = false,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/v1${path}`, {
      ...options,
      credentials: "include",
      cache: "no-store",
      headers: {
        ...(options.body instanceof FormData
          ? {}
          : { "Content-Type": "application/json" }),
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(
      "Không thể kết nối máy chủ. Vui lòng kiểm tra kết nối mạng.",
      0,
      "offline",
    );
  }
  if (
    response.status === 401 &&
    retry &&
    ![
      "/auth/login",
      "/auth/register",
      "/auth/refresh",
      "/auth/logout",
    ].includes(path)
  ) {
    if (!refreshPromise) {
      // Serialize refresh across tabs too; refresh tokens rotate on every use.
      const refresh = async () => {
        const check = await fetch("/api/v1/auth/me", {
          credentials: "include",
        });
        if (check.ok) return true;
        return (
          await fetch("/api/v1/auth/refresh", {
            method: "POST",
            credentials: "include",
          })
        ).ok;
      };
      refreshPromise = (async () =>
        typeof navigator !== "undefined" && navigator.locks
          ? await navigator.locks.request("vstep-auth-refresh", refresh)
          : await refresh())()
        .catch(() => false)
        .finally(() => {
          refreshPromise = null;
        });
    }
    if (await refreshPromise) return api<T>(path, options, false, binary);
  }
  if (response.ok && binary) return (await response.blob()) as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new ApiError(
      typeof data.detail === "string"
        ? data.detail
        : "Yêu cầu chưa thực hiện được. Vui lòng thử lại.",
      response.status,
      data.code,
      data,
    );
  return data as T;
}
export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) });

export const audioBlob = (path: string, options: RequestInit = {}) =>
  api<Blob>(path, options, true, true);
