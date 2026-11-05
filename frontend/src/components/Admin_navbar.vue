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
            <a
              class="nav-link active"
              aria-current="page"
              href="/admin/manager-requests"
              >ManagerRequests</a
            >
          </li>

          <li class="nav-item">
            <router-link class="nav-link" to="/manager/summary">Summary</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/manager/coupons">Coupons</router-link>
          </li>
          <li class="nav-item">
            <a class="nav-link" href="#" @click.prevent="download_report">Report</a>
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
import { downloadSalesReport } from "@/report";
export default {
  props: {},
  data() {
    return {
      data: [],
      categories: [],
      is_manager: sessionStorage.getItem("is_manager"),
    };
  },
  mounted() {},
  methods: {
    goHome() {
      if (this.$route.path === "/admin/dashboard") {
        window.location.reload();
      } else {
        this.$router.push("/admin/dashboard");
      }
    },
    logout() {
      sessionStorage.removeItem("accessToken");
      sessionStorage.removeItem("role");
      sessionStorage.removeItem("signed");
      sessionStorage.removeItem("name");
      alert("Logged out successfully");
      this.$router.push("/");
    },
    async download_report() {
      try {
        await downloadSalesReport();
      } catch (error) {
        alert(error.message || "Could not download the report.");
      }
    },
  },
};
</script>
