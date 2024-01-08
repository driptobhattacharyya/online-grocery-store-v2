// Your Vue.js component

<template>
  <div class="container py-4 py-xl-5 mx-auto col-xl-3">
    <h2>Login</h2>
    <br />
    <br />
    <form @submit.prevent="login">
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Email</label>
        <input
          v-model="email"
          type="username"
          class="form-control"
          name="email"
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
      <p>Don't have an account? <a href="/signup">Create one</a></p>
      <p>Are you the admin? <a href="/admin/login">Click here</a></p>
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
    async login() {
      axios
        .post("http://localhost:5000/api/login", {
          email: this.email,
          password: this.password,
        })
        .then((response) => {
          console.log(response.data)

          const accessToken = response.data.access_token;
          sessionStorage.setItem("accessToken", accessToken);
          if (response.data.is_manager){
            alert("Welcome manager")
            sessionStorage.setItem("is_manager", true);
            this.$router.push("/StoreManager/dashboard")
          } else {
            sessionStorage.setItem("signed", true);
            sessionStorage.setItem("name", response.data.name);
            this.$router.push("/");
          }          
        })
        .catch((error) => {
          console.error(error.response.data.error);
        });
    },
  },
};
</script>
