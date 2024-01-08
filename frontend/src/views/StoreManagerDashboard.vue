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
            <a href="/admin/add_product" class="btn btn-primary">Add Product</a>
          </div>
        </div>
      </div>
    </div>

    <div class="container">
      <h2 class="mb-4">Existing Inventory</h2>
      <div class="row row-cols-1 row-cols-md-3 g-4">
        <div v-for="category in categories" :key="category.id">
          <div
            class="card-body d-flex justify-content-between align-items-center"
          >
            <h3>{{ category.category_name }}</h3>
          </div>
          <div v-for="product in category.products" :key="product.id">
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
                  <div @click="editProduct(product)" class="btn btn-primary">
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
// import Admin_navbar from "@/components/Admin_navbar.vue";

export default {
  name: "StoreManagerDashboard",
  components: {
    Manager_navbar,
  },
  data() {
    return {
      categories: [],
      token: sessionStorage.getItem("accessToken"),
      is_manager: sessionStorage.getItem("is_manager"),
      newCategory: "",
    };
  },
  mounted() {
    this.getIems();
    console.log(this.token);
  },
  methods: {
    getIems() {
      console.log(this.is_manager);
      axios
        .get("http://localhost:5000/api/manager/dashboard", {
          params: {
            is_manager: this.is_manager,
          },
          mode: "no-cors",
          headers: {
            Authorization: "Bearer " + this.token,
          },
        })
        .then((response) => {
          if (response.data.error) {
            alert(response.error);
          } else {
            this.categories = response.data.categories;
          }
        })
        .catch((error) => {
          alert(error);
        });
    },
    editProduct(product) {
      console.log(product);
      sessionStorage.setItem("productName", product.product_name)
      sessionStorage.setItem("productQuantity", product.quantity);
      sessionStorage.setItem("productUnit", product.unit)
      sessionStorage.setItem("productPrice", product.price);
      sessionStorage.setItem("productMnfdate", product.manufacture_date);
      sessionStorage.setItem("productExpdate", product.expiry_date);
      this.$router.push(`/api/manager/edit_product/${product.productID}`);
    },
    deleteProduct(product) {
      // Confirm deletion with user
      if (
        confirm(`Are you sure you want to delete '${product.product_name}'?`)
      ) {
        try {
          console.log(product.productID);
          // Send delete request to backend
          axios
            .post(
              "http://localhost:5000/api/manager/delete_product",
              {
                product_id: product.productID,
              },
              {
                params: {
                  is_manager: this.is_manager,
                },
                mode: "no-cors",
                headers: {
                  Authorization: "Bearer " + this.token,
                },
              }
            )
            .then((response) => {
              if (false) {
                alert(response.error);
              } else {
                window.location.reload();
                alert(
                  `Product '${product.product_name}' deleted successfully!`
                );
              }
            //   windows.location.reload();
            })
            .catch((error) => {
              console.error(error);
              alert(`Error deleting product: ${error.message}`);
            });
        } catch {
          console.log("Some error occured");
        }
      }
    },
  },
};
</script>
