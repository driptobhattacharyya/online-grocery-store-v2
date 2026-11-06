import { createRouter, createWebHistory } from "vue-router";
import { getRole, loginPathFor } from "../auth";

// Every page is loaded on demand so the initial bundle only carries the shell.
const User_products = () => import("../components/User_products.vue");
const Login = () => import("../views/Login.vue");
const Signup = () => import("../views/Signup.vue");
const Shopping_cart = () => import("../views/Shopping_cart.vue");
const Dashboard2 = () => import("../views/Dashboard2.vue");
const OrderConfirmation = () => import("../views/OrderConfirmation.vue");
const AdminDashboard = () => import("../views/AdminDashboard.vue");
const EditProduct = () => import("../components/EditProduct.vue");
const AddProduct = () => import("../components/AddProduct.vue");
const AdminLogin = () => import("../components/AdminLogin.vue");
const ManagerRequests = () => import("../views/ManagerRequests.vue");
const StoreManagerDashboard = () => import("../views/StoreManagerDashboard.vue");
const AboutView = () => import("../views/AboutView.vue");
const NotFound = () => import("../views/NotFound.vue");

const SHOPPER = { requiresAuth: true, roles: ["user"] };
const MANAGER = { requiresAuth: true, roles: ["manager"] };
const ADMIN = { requiresAuth: true, roles: ["admin"] };
const STAFF = { requiresAuth: true, roles: ["manager", "admin"] };

const routes = [
  { path: "/", name: "home", component: User_products, meta: { title: "Shop" } },
  { path: "/about", name: "about", component: AboutView, meta: { title: "About" } },
  { path: "/login", name: "login", component: Login, meta: { title: "Log in" } },
  { path: "/signup", name: "signup", component: Signup, meta: { title: "Sign up" } },
  {
    path: "/shopping_cart",
    name: "shopping_cart",
    component: Shopping_cart,
    meta: { ...SHOPPER, title: "Your cart" },
  },
  {
    path: "/dashboard",
    name: "User_Dashboard2",
    component: Dashboard2,
    meta: { ...SHOPPER, title: "Your orders" },
  },
  {
    path: "/order-confirmation",
    name: "OrderConfirmation",
    component: OrderConfirmation,
    meta: { ...SHOPPER, title: "Order confirmed" },
  },
  {
    path: "/admin/login",
    name: "AdminLogin",
    component: AdminLogin,
    meta: { title: "Admin log in" },
  },
  {
    path: "/admin/dashboard",
    name: "AdminDashboard",
    component: AdminDashboard,
    meta: { ...ADMIN, title: "Admin dashboard" },
  },
  {
    path: "/admin/add_product",
    name: "AddProduct",
    component: AddProduct,
    meta: { ...ADMIN, title: "Add product" },
  },
  {
    path: "/admin/manager-requests",
    name: "ManagerRequests",
    component: ManagerRequests,
    meta: { ...ADMIN, title: "Manager requests" },
  },
  {
    path: "/StoreManager/dashboard",
    name: "StoreManagerDashboard",
    component: StoreManagerDashboard,
    meta: { ...MANAGER, title: "Manager dashboard" },
  },
  {
    // Shared by managers and admins. Must not start with /api: Flask answers
    // /api/* itself, so a hard refresh there would never reach the SPA.
    path: "/manage/edit_product/:product_id",
    name: "EditProduct",
    component: EditProduct,
    meta: { ...STAFF, title: "Edit product" },
  },
  {
    // Old path, kept so existing links keep working during client-side
    // navigation (a hard refresh on it still hits Flask's /api 404).
    path: "/api/manager/edit_product/:product_id",
    redirect: (to) => ({
      name: "EditProduct",
      params: { product_id: to.params.product_id },
    }),
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: NotFound,
    meta: { title: "Page not found" },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: (to, from, saved) => saved || { top: 0 },
});

router.beforeEach((to) => {
  const meta = to.meta || {};
  if (!meta.requiresAuth) return true;

  const role = getRole();
  if (!role) {
    return { path: loginPathFor(meta.roles), query: { redirect: to.fullPath } };
  }
  if (meta.roles && !meta.roles.includes(role)) {
    // Logged in, but this area belongs to another role.
    return "/";
  }
  return true;
});

const APP_NAME = "Grocery Store";

router.afterEach((to) => {
  document.title = to.meta && to.meta.title ? `${to.meta.title} · ${APP_NAME}` : APP_NAME;
});

export default router;
