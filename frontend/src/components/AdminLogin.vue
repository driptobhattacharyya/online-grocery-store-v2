<template>
  <div class="container py-4 py-xl-5 mx-auto col-xl-3">
    <h2>Admin Login</h2>
    <br />
    <br />
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

export default {
  data() {
    return {
      email: "",
      password: "",
    };
  },
  methods: {
    async admin_login() {
      axios
        .post("http://localhost:5000/api/admin/login", {
          email: this.email,
          password: this.password,
        })
        .then((response) => {
          const accessToken = response.data.access_token;
          sessionStorage.setItem("accessToken", accessToken);
          sessionStorage.setItem("admin", true);
          this.$router.push("/admin/dashboard");
        })
        .catch((error) => {
          console.error(error.response.data.error);
        });
    },
  },
};
</script>
