// Single source of truth for the client-side session.
//
// Login.vue stores `accessToken` plus either `is_manager` (managers) or
// `signed` + `name` (shoppers); AdminLogin.vue stores `accessToken` + `admin`.
// Everything that needs to know "who is logged in" should go through here.

const AUTH_KEYS = ["accessToken", "signed", "name", "is_manager", "admin"];

function read(key) {
  try {
    return window.sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

// sessionStorage stores strings, so `setItem("admin", true)` becomes "true".
function isTrue(key) {
  return read(key) === "true";
}

export function getToken() {
  const token = read("accessToken");
  return token && token !== "undefined" && token !== "null" ? token : null;
}

export function isAuthenticated() {
  return getToken() !== null;
}

/** @returns {'admin' | 'manager' | 'user' | null} */
export function getRole() {
  if (!isAuthenticated()) return null;
  if (isTrue("admin")) return "admin";
  if (isTrue("is_manager")) return "manager";
  return "user";
}

/** Where a given role should land by default. */
export function homeFor(role) {
  if (role === "admin") return "/admin/dashboard";
  if (role === "manager") return "/StoreManager/dashboard";
  return "/";
}

/** Login page that serves the given set of allowed roles. */
export function loginPathFor(roles) {
  return Array.isArray(roles) && roles.length === 1 && roles[0] === "admin"
    ? "/admin/login"
    : "/login";
}

/** Clears every auth key, whichever role set them. */
export function logout() {
  try {
    AUTH_KEYS.forEach((key) => window.sessionStorage.removeItem(key));
  } catch {
    /* storage unavailable: nothing to clear */
  }
}
