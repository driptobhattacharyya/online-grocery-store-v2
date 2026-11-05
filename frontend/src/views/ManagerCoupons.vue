<template>
  <div>
    <component :is="navbar" />
    <div class="container py-4 text-start">
      <h1>Coupon codes</h1>
      <p>Customers enter these in the cart. Each code is a percentage off, once per customer.</p>
      <form class="row g-2 mb-4" @submit.prevent="createCoupon">
        <div class="col-md-4">
          <input class="form-control" v-model="code" placeholder="Coupon code" required />
        </div>
        <div class="col-md-3">
          <input class="form-control" type="number" min="1" max="100" v-model.number="discount" placeholder="Percent off" required />
        </div>
        <div class="col-md-2">
          <button class="btn btn-primary" type="submit">Add coupon</button>
        </div>
      </form>
      <table class="table">
        <thead>
          <tr>
            <th>Code</th>
            <th>Discount</th>
            <th>Times used</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="coupon in coupons" :key="coupon.coupon_code">
            <td>{{ coupon.coupon_code }}</td>
            <td>{{ coupon.discount_percentage }}%</td>
            <td>{{ coupon.count }}</td>
            <td>
              <button class="btn btn-sm btn-outline-danger" @click="remove(coupon.coupon_code)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Admin_navbar from "@/components/Admin_navbar.vue";
import Manager_navbar from "@/components/Manager_navbar.vue";

export default {
  components: { Admin_navbar, Manager_navbar },
  data() {
    return {
      coupons: [],
      code: "",
      discount: 10,
    };
  },
  computed: {
    navbar() {
      return sessionStorage.getItem("role") === "admin" ? "Admin_navbar" : "Manager_navbar";
    },
  },
  mounted() {
    this.load();
  },
  methods: {
    load() {
      axios.get("/api/manager/coupons").then((response) => {
        this.coupons = response.data.coupons;
      });
    },
    createCoupon() {
      axios
        .post("/api/manager/coupons", {
          coupon_code: this.code,
          discount_percentage: this.discount,
        })
        .then(() => {
          this.code = "";
          this.load();
        })
        .catch((error) => alert(error.response?.data?.error || "Could not add the coupon."));
    },
    remove(code) {
      if (!confirm(`Delete ${code}?`)) return;
      axios.delete(`/api/manager/coupons/${code}`).then(() => this.load());
    },
  },
};
</script>
