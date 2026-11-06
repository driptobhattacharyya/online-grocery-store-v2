<template>
  <nav class="navbar navbar-expand-lg">
    <div class="container-fluid">
      <a class="navbar-brand" href="#">Welcome Admin</a>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <a
              href="#"
              class="nav-link active"
              aria-current="page"
              @click="goHome"
              >Home</a
            >
          </li>

          <li class="nav-item">
            <router-link class="nav-link active" to="/admin/manager-requests"
              >ManagerRequests</router-link
            >
          </li>

          <li class="nav-item">
            <a
              class="nav-link active"
              aria-current="page"
              href="#"
              @click="download_report"
              >Report</a
            >
          </li>

          <li class="nav-item">
            <a class="nav-link" href="#" @click="logout">Logout</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
import { getToken, logout } from "@/auth";

export default {
  methods: {
    goHome() {
      if (this.$route.path === "/admin/dashboard") {
        window.location.reload();
      } else {
        this.$router.push("/admin/dashboard");
      }
    },
    logout() {
      logout();
      alert("Logged out successfully");
      this.$router.push("/");
    },
    async download_report() {
      try {
        const response = await fetch("/api/manager/prepare_report", {
          headers: { Authorization: `Bearer ${getToken()}` },
        });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(body.error || `Report download failed (HTTP ${response.status})`);
        }
        const url = window.URL.createObjectURL(await response.blob());
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", "order_report.csv");
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error("Error downloading order report:", error);
        alert(error.message);
      }
    },
  },
};
</script>
