/** Translate links saved before the frontend moved to static hosting. */
export function staticPageUrl(url: string): string {
  const question = url.match(/^\/admin\/questions\/([^/?]+)\/([^/?]+)$/);
  if (question)
    return `/admin/question?skill=${encodeURIComponent(question[1])}&id=${encodeURIComponent(question[2])}`;
  const user = url.match(/^\/admin\/users\/([^/?]+)(\?.*)?$/);
  if (user)
    return `/admin/user?id=${encodeURIComponent(user[1])}${user[2] ? `&${user[2].slice(1)}` : ""}`;
  const detail = url.match(/^\/my-questions\/([^/?]+)$/);
  if (detail) return `/my-questions/detail?id=${encodeURIComponent(detail[1])}`;
  const match = url.match(
    /^\/(exam|result|speaking\/(?:exam|result)|reading\/(?:exam|result)|learning\/(?:weaknesses|practice)|vocabulary\/review)\/([^/?]+)$/,
  );
  return match ? `/${match[1]}?id=${encodeURIComponent(match[2])}` : url;
}
