import { createApp } from "vue";
import axios from "axios";
import App from "./App.vue";
import router from "./router";
import store from "./store";

axios.defaults.baseURL = process.env.VUE_APP_API_BASE || "";
axios.interceptors.request.use((config) => {
  const token = sessionStorage.getItem("accessToken");
  if (token && !(config.headers && config.headers.Authorization)) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

createApp(App).use(store).use(router).mount("#app");
