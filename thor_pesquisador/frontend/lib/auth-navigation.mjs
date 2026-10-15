export const SESSION_EXPIRED = "thor:session-expired";

export function safeReturnPath(value) {
  if(typeof value !== "string" || !value.startsWith("/") || value.startsWith("//")) return "/dashboard";
  try {
    const decoded = decodeURIComponent(value);
    if(decoded.startsWith("//") || /[\\\u0000-\u001f\u007f]/.test(decoded)) return "/dashboard";
    const url = new URL(value, "http://thor.local");
    if(url.origin !== "http://thor.local" || /^\/login(?:\/|$)/.test(decodeURIComponent(url.pathname))) return "/dashboard";
    return url.pathname + url.search + url.hash;
  } catch {return "/dashboard";}
}

export function loginPath(value) {
  return "/login?next=" + encodeURIComponent(safeReturnPath(value));
}

export function notifySessionExpired() {
  if(typeof window !== "undefined") window.dispatchEvent(new Event(SESSION_EXPIRED));
}
