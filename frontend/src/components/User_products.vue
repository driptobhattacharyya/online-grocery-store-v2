<template>
  <div>
    <div class="container-fluid bg-light-green">
      <div class="page-header">
        <h1>Welcome to <span class="text-success">7 to 11</span></h1>
        <p>Start shopping for your favorite groceries!</p>
      </div>
    </div>
    <Navbar :user="name" :signed="signed" @ChildEvent="handleChildEvent" />
    <div>
      <div class="container">
        <RecommendationRow title="Picked for you" :items="recommendations" :signed="signed" />
        <div class="row row-cols-1 row-cols-md-3 g-4">
          <ProductCard
            v-for="product in products"
            :key="product.productID"
            :product="product"
            :signed="signed"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import ProductCard from "@/components/ProductCard.vue";
import Navbar from "@/components/Navbar.vue";
import RecommendationRow from "@/components/RecommendationRow.vue";
import "@/assets/style.css";

export default {
  components: {
    ProductCard,
    Navbar,
    RecommendationRow,
  },
  data() {
    return {
      loading: false,
      products: [],
      recommendations: [],
      name: "",
      signed: false,
    };
  },
  mounted() {
    this.signed = sessionStorage.getItem("signed") === "true";
    this.name = sessionStorage.getItem("name") || "";
    this.loading = true;
    axios
      .get("/api/user_dashboard")
      .then((response) => {
        this.products = response.data.products;
      })
      .finally(() => {
        this.loading = false;
      });
    const recommendationUrl = this.signed ? "/api/recommendations/for-you" : "/api/recommendations/popular";
    axios
      .get(recommendationUrl)
      .then((response) => {
        this.recommendations = response.data.recommendations || [];
      })
      .catch(() => {
        axios.get("/api/recommendations/popular").then((response) => {
          this.recommendations = response.data.recommendations || [];
        });
      });
  },
  methods: {
    handleChildEvent(products) {
      this.products = products || [];
    },
  },
};
</script>

<style>
.page-header {
  background-image: url("../assets/Banner_pic.jpg");
  background-size: cover;
  background-position: center;
  padding: 60px 0;
  text-align: center;
  border-bottom: 5px solid #d2d2d2;
}
.page-header h1 {
  font-size: 36px;
  margin-bottom: 10px;
  text-align: left;
  margin-left: 100px;
}
.page-header p {
  font-size: 18px;
  text-align: left;
  margin-left: 100px;
}
.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.305);
}
</style>
