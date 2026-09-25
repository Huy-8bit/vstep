function handler(event) {
  var request = event.request;
  var uri = request.uri;
  if (uri === "/") {
    request.uri = "/index.html";
  } else if (uri.indexOf(".") === -1 && uri.indexOf("/_next/") !== 0) {
    // Next static export emits /admin.html, /reading.html, etc.
    request.uri = uri.replace(/\/$/, "") + ".html";
  }
  return request;
}
