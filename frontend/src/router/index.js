import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import User_products from "../components/User_products.vue";
import Login from "../views/Login.vue"
import Shopping_cart from "../views/Shopping_cart.vue"
import Dashboard2 from "../views/Dashboard2.vue"
import Signup from "../views/Signup.vue"
import OrderConfirmation from "../views/OrderConfirmation.vue"

import AdminDashboard from "../views/AdminDashboard.vue"
import EditProduct from "../components/EditProduct.vue"
import AddProduct from "../components/AddProduct.vue"
import AdminLogin from "../components/AdminLogin.vue"
import ManagerRequests from "../views/ManagerRequests.vue"

import StoreManagerDashboard from "../views/StoreManagerDashboard.vue"

const routes = [
  {
    path: "/",
    name: "home",
    component: User_products,
  },
  {
    path: "/about",
    name: "about",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: function () {
      return import(/* webpackChunkName: "about" */ "../views/AboutView.vue");
    },
  },
  {
    path: "/login",
    name: "login",
    component: Login,
  },
  {
    path: "/signup",
    name: "signup",
    component: Signup,
  },
  {
    path:"/shopping_cart",
    name:"shopping_cart",
    component: Shopping_cart
  },
  {
    path:"/dashboard",
    name:"User_Dashboard2",
    component: Dashboard2
  },
  {
    path: '/order-confirmation',
    name: 'OrderConfirmation',
    component: OrderConfirmation,
  },
  {
    path: "/admin/dashboard",
    name: "AdminDashboard",
    component: AdminDashboard
  },
  {
    path: "/admin/add_product",
    name: "AddProduct",
    component: AddProduct
  },
  {
    path: "/api/manager/edit_product/:product_id",
    name: "EditProduct",
    component: EditProduct,
    // props: true
  },
  {
    path: "/admin/login",
    name: "AdminLogin",
    component: AdminLogin,
  },
  {
    path: "/StoreManager/dashboard",
    name: "StoreManagerDashboard",
    component: StoreManagerDashboard
  },
  {
    path: "/admin/manager-requests",
    name: "ManagerRequests",
    component: ManagerRequests
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
