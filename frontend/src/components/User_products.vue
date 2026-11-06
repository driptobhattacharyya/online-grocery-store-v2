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
        <p v-if="!loading && products.length === 0" class="text-center mt-4">No products to show.</p>
        <div class="row row-cols-1 row-cols-md-3 g-4">
          <ProductCard
            v-for="product in products"
            :key="product[0]"
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

// ProductCard reads products as rows: [productID, name, manufacture_date,
// expiry_date, price, dynamic_price, is_recommended, categoryID, unit,
// inventoryId, productID, stock]. Search results arrive as objects.
function toRow(product) {
  if (Array.isArray(product)) return product;
  return [
    product.productID,
    product.name,
    product.manufacture_date,
    product.expiry_date,
    product.price,
    product.dynamic_price,
    product.is_recommended,
    product.categoryID,
    product.unit,
    null,
    product.productID,
    product.stock ?? 0,
  ];
}

export default {
  components: {
    ProductCard,
    Navbar,
  },
  data() {
    return {
      loading: false,
      products: [],
      name: "",
      signed: false,
    };
  },
  mounted() {
    this.signed = sessionStorage.getItem("signed") === "true";
    this.name = sessionStorage.getItem("name");
    this.loadProducts();
  },
  methods: {
    async loadProducts() {
      this.loading = true;
      try {
        const response = await axios.get("/api/user_dashboard");
        this.products = response.data.products;
      } catch (error) {
        console.error("Error fetching products:", error);
        alert(error?.response?.data?.error || "Could not load products.");
      } finally {
        this.loading = false;
      }
    },
    handleChildEvent(products) {
      this.products = (products || []).map(toRow);
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
