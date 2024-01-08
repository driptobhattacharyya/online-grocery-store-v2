<template>
  <div>
    <div class="container-fluid bg-light-green">
      <div class="page-header">
        <h1>Welcome to <span class="text-success">7 to 11</span></h1>
        <p>Start shopping for your favorite groceries!</p>
      </div>
    </div>
    <Navbar
      :user="received_datadata.user"
      :categories="received_datadata.categories"
      :signed="received_data.signed"
    />
    <div>
      <div class="container">
        <div class="row row-cols-1 row-cols-md-3 g-4">
          <ProductCard
            v-for="product in received_data.products"
            :product="product"
            :signed="received_data.signed"
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
import "@/assets/style.css";

export default {
  components: {
    ProductCard,
    Navbar,
  },
  data() {
    return {
      received_data: [],
    };
  },
  mounted() {
    // Make a GET request to your Flask API endpoint
    if (!this.received_data.length) {
      axios
        .get("http://localhost:5000/api/user_dashboard")
        .then((response) => {
          this.received_data = response.data;
          console.log(received_data.user, received_data.signed);
        })
        .catch((error) => {
          console.error("Error fetching data:", error);
        });
    }
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
