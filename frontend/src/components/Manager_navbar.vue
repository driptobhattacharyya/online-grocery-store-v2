<template>
    <nav class="navbar navbar-expand-lg">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">Welcome Manager</a>
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
  import axios from "axios";
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
        if (this.$route.path === "/StoreManager/dashboard") {
          window.location.reload();
        } else {
          this.$router.push("/StoreManager/dashboard");
        }
      },
      logout() {
        sessionStorage.removeItem("accessToken");
        sessionStorage.removeItem("is_manager");
        sessionStorage.removeItem("signed");
      sessionStorage.removeItem("name");
        alert("Logged out successfully");
        this.$router.push("/");
      },
      async download_report() {
        const token = sessionStorage.getItem("access_token");
        fetch("http://localhost:5000/api/manager/prepare_report"
        // , {
        //   headers: {
        //     "Authorization": `Bearer ${this.token}`,
        //   },}
        )
          .then((response) => response.blob())
          .then((blob) => {
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", "order_report.csv");
            document.body.appendChild(link);
            link.click();
          })
          .catch((error) => {
            console.error("Error downloading order report:", error);
          });
      },
    },
  };
  </script>
  