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
        <div class="row row-cols-1 row-cols-md-3 g-4">
          <ProductCard
            v-for="product in products"
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
import "@/assets/style.css";

export default {
  components: {
    ProductCard,
    Navbar,
  },
  data() {
    return {
      received_data: [],
      loading: false,
      products: [],
      name: "",
      signed: false,
    };
  },
  mounted() {
    this.signed = sessionStorage.getItem("signed");
    this.name = sessionStorage.getItem("name");
    if (!this.loading && !this.received_data.length) {
      this.loading = true;
      axios
        .get("http://localhost:5000/api/user_dashboard")
        .then((response) => {
          this.received_data = response.data;
          this.products = this.received_data.products;
        })
        .catch((error) => {
          console.error("Error fetching data:", error);
        })
        .finally(() => {
          this.loading = false;
        });
    }
  },
  methods: {
    handleChildEvent(products) {
      console.log("Printing 1 product " + products[0]);
      if (products[0].categoryID) {
        console.log("Coming through...");
        var new_products = [];
        for (var i = 0; i < products.length; i++) {
          var product = products[i];
          var new_product = [
            product.productID,
            product.name,
            product.manufacture_date,
            product.expiry_date,
            product.price,
            product.dynamic_price,
            product.is_recommended,
            product.categoryID,
            product.unit,
          ];
          new_products.push(new_product);
        }
        this.products = new_products;
      } else {
        this.products = products;
      }
      console.log(this.products);
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
