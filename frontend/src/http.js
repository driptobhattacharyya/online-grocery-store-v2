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

// The API answers every rejected token (missing, expired, malformed, badly
// signed, or issued against a database that has since been reset) with
// 401 `{ error }` (see the JWT loaders in app.py).
function isSessionRejected(error) {
  return Boolean(error.response && error.response.status === 401);
}

// The login page for the session that just died: admins log in at
// /admin/login, shoppers and managers at /login. Only without a stored role
// (nothing to go on) is the current path used to guess.
function loginPathAfterExpiry(role, currentPath) {
  if (role) return loginPathFor(role === "admin" ? ["admin"] : null);
  return loginPathFor(currentPath.startsWith("/admin") ? ["admin"] : null);
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
        const target = loginPathAfterExpiry(getRole(), current.path);
        logout();
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
