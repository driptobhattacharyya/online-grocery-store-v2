import axios from "axios";
import router from "./router";
import { getRole, logout, loginPathFor } from "./auth";

// Credential endpoints legitimately answer 401 for a bad password; those must
// reach the form's own error handling without a redirect.
const AUTH_ENDPOINTS = ["/api/login", "/api/admin/login", "/api/signup"];

function isAuthEndpoint(url = "") {
  const path = url
    .replace(/^https?:\/\/[^/]+/, "")
    .split("?")[0]
    .replace(/\/+$/, "");
  return AUTH_ENDPOINTS.includes(path);
}

// flask-jwt-extended answers 401 for a missing/expired token but 422 for a
// malformed or badly signed one (e.g. after JWT_SECRET_KEY rotates), always
// with a `{ msg }` body. App endpoints never use `msg`, so a 422 with that
// shape on a request that carried a token means the session is dead too.
function isSessionRejected(error) {
  const res = error.response;
  if (!res) return false;
  if (res.status === 401) return true;
  const headers = (error.config && error.config.headers) || {};
  const sentToken = Boolean(
    typeof headers.get === "function"
      ? headers.get("Authorization")
      : headers.Authorization || headers.authorization
  );
  return (
    res.status === 422 &&
    sentToken &&
    res.data &&
    typeof res.data.msg === "string"
  );
}

let installed = false;

/**
 * On a rejected session (see above) from any non-login endpoint: clear the session and send the user to
 * the matching login page (with ?redirect=back). The promise is still rejected
 * so call sites' own .catch() handlers run.
 */
export function installHttpInterceptors(instance = axios) {
  if (installed) return;
  installed = true;
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      const url = error.config && error.config.url;
      if (isSessionRejected(error) && !isAuthEndpoint(url)) {
        const current = router.currentRoute.value;
        const adminArea =
          getRole() === "admin" || current.path.startsWith("/admin");
        logout();
        const target = loginPathFor(adminArea ? ["admin"] : null);
        if (current.path !== target) {
          router.replace({
            path: target,
            query: current.fullPath !== "/" ? { redirect: current.fullPath } : {},
          });
        }
      }
      return Promise.reject(error);
    }
  );
}
