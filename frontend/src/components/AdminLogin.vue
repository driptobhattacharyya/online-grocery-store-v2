<template>
  <div class="container py-4 py-xl-5 mx-auto col-xl-3">
    <h2>Admin Login</h2>
    <br />
    <br />
    <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>
    <form @submit.prevent="admin_login">
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Username</label>
        <input
          v-model="email"
          type="username"
          class="form-control"
          name="username"
          aria-describedby="emailHelp"
          required
        />
      </div>
      <div class="mb-3">
        <label for="exampleInputPassword1" class="form-label">Password</label>
        <input
          v-model="password"
          class="form-control"
          type="password"
          required
        />
      </div>
      <div>
        <button type="submit" class="btn btn-primary">Login</button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from "axios";
import "@/assets/style.css";
import { logout } from "@/auth";

// Only follow same-origin, path-only redirects ("/x", never "//host", "/\\host" or "http://").
function safeRedirect(value, fallback) {
  return typeof value === "string" && value.startsWith("/") && !value.startsWith("//") && !value.startsWith("/\\")
    ? value
    : fallback;
}

function errorMessage(error) {
  return error?.response?.data?.error || "Login failed. Please try again.";
}

export default {
  data() {
    return {
      email: "",
      password: "",
      error: "",
    };
  },
  methods: {
    async admin_login() {
      this.error = "";
      try {
        const response = await axios.post("/api/admin/login", {
          email: this.email,
          password: this.password,
        });
        logout(); // drop any keys left by a previous role
        sessionStorage.setItem("accessToken", response.data.access_token);
        sessionStorage.setItem("admin", true);
        this.$router.push(safeRedirect(this.$route.query.redirect, "/admin/dashboard"));
      } catch (error) {
        this.error = errorMessage(error);
      }
    },
  },
};
</script>
