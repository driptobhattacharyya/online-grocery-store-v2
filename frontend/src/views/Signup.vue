// Your Vue.js component

<template>
  <div class="container py-4 py-xl-5 mx-auto col-xl-3">
    <h2>Signup</h2>
    <br />
    <br />
    <form @submit.prevent="signup">
      <div class="mb-3">
        <label for="name" class="form-label">Name</label>
        <input
          type="username"
          class="form-control"
          name="name"
          v-model="name"
          aria-describedby="emailHelp"
          required
        />
      </div>
      <div class="mb-3">
        <label for="number" class="form-label">Phone Number</label>
        <input
          type="username"
          class="form-control"
          name="phoneno"
          v-model="phoneNo"
          aria-describedby="emailHelp"
          required
        />
      </div>
      <div class="mb-3">
        <label for="Address" class="form-label">Address</label>
        <input
          type="username"
          v-model="address"
          class="form-control"
          name="address"
          aria-describedby="emailHelp"
          required
        />
      </div>
      <div class="mb-3">
        <label for="exampleInputEmail1" class="form-label">Email</label>
        <input
          v-model="email"
          type="email"
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
      <div class="mb-3">
        <label for="exampleInputPassword1" class="form-label"
          >Confirm Password</label
        >
        <input
          type="password"
          class="form-control"
          name="confirm_password"
          v-model="confirm_password"
          required
        />
      </div>
      <div>
        <button type="submit" class="btn btn-primary">Sign up</button>
      </div>
      <p>Already have an account? <a href="/login">Login</a></p>
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
      name: "",
      phoneNo: "",
      address: "",
      email: "",
      password: "",
      confirm_password:""
    };
  },
  methods: {
    async signup() {
      if (this.password !== this.confirm_password){
        alert("Passwords do not match")
      } else{
        axios
          .post("http://localhost:5000/api/signup", {
            name: this.name,
            phoneNo: this.phoneNo,
            address: this.address,
            email: this.email,
            password: this.password,
          })
          .then((response) => {
            if (response.data.message == "Success"){
              console.log(response.data);
              alert("Welcome aboard! Now you have to login.")
              this.$router.push("/login");            
            }
            else{
              alert(response.data.Error)
            }
          })
          .catch((error) => {
            alert(error.response.data.error);
          });        
      }
    },
  },
};
</script>
