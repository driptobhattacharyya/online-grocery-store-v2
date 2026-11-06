<template>
  <Manager_navbar />
  <div>
    <br />
    <h1 class="mb-4">Store Manager Dashboard</h1>
    <div class="row">
      <div class="col-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Create a New Product</h5>
            <router-link to="/admin/add_product" class="btn btn-primary">Add Product</router-link>
          </div>
        </div>
      </div>
    </div>

    <div class="container">
      <h2 class="mb-4">Existing Inventory</h2>
      <div class="row row-cols-1 row-cols-md-3 g-4">
        <div v-for="category in categories" :key="category.categoryID">
          <div
            class="card-body d-flex justify-content-between align-items-center"
          >
            <h3>{{ category.category_name }}</h3>
          </div>
          <div v-for="product in category.products" :key="product.productID">
            <div class="col">
              <div class="card">
                <div class="card-body">
                  <h3 class="card-title">{{ product.product_name }}</h3>
                  <h5 class="card-title">
                    Stock: {{ product.quantity }} {{ product.unit }}s
                  </h5>
                  <p class="card-text">
                    Price: ₹ {{ product.price }}/{{ product.unit }}
                  </p>
                  <p class="card-text">
                    Manufacture Date: {{ product.manufacture_date }}
                  </p>
                  <p class="card-text">
                    Expiry Date: {{ product.expiry_date }}
                  </p>
                  <p class="card-text">{{ product.description }}</p>
                  <div @click="editProduct(product, category)" class="btn btn-primary">
                    Edit Product
                  </div>
                  <div
                    @click="deleteProduct(product)"
                    class="btn btn-darkgreen"
                  >
                    Delete Product
                  </div>
                </div>
              </div>
            </div>
            <br />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import "@/assets/style_manager.css";
import Manager_navbar from "@/components/Manager_navbar.vue";

function errorMessage(error, fallback) {
  return error?.response?.data?.error || fallback;
}

export default {
  name: "StoreManagerDashboard",
  components: {
    Manager_navbar,
  },
  data() {
    return {
      categories: [],
      token: sessionStorage.getItem("accessToken"),
    };
  },
  mounted() {
    this.getItems();
  },
  methods: {
    authHeaders() {
      return { headers: { Authorization: "Bearer " + this.token } };
    },
    async getItems() {
      try {
        const response = await axios.get("/api/manager/dashboard", this.authHeaders());
        this.categories = response.data.categories;
      } catch (error) {
        console.error("Error loading inventory:", error);
        alert(errorMessage(error, "Could not load the inventory."));
      }
    },
    editProduct(product, category) {
      sessionStorage.setItem("productName", product.product_name);
      sessionStorage.setItem("productCategory", category.category_name);
      sessionStorage.setItem("productQuantity", product.quantity);
      sessionStorage.setItem("productUnit", product.unit);
      sessionStorage.setItem("productPrice", product.price);
      sessionStorage.setItem("productMnfdate", product.manufacture_date);
      sessionStorage.setItem("productExpdate", product.expiry_date);
      this.$router.push(`/manage/edit_product/${product.productID}`);
    },
    async deleteProduct(product) {
      if (!confirm(`Are you sure you want to delete '${product.product_name}'?`)) return;
      try {
        await axios.post(
          "/api/manager/delete_product",
          { product_id: product.productID },
          this.authHeaders()
        );
        alert(`Product '${product.product_name}' deleted successfully!`);
        this.getItems();
      } catch (error) {
        alert(errorMessage(error, "Could not delete the product."));
      }
    },
  },
};
</script>
