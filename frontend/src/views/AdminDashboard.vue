<template>
  <Admin_navbar />
  <div>
    <br />
    <h1 class="mb-4">Admin Dashboard</h1>
    <div class="row">
      <div class="col-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Create a New Product</h5>
            <a href="/admin/add_product" class="btn btn-primary">Add Product</a>
          </div>
        </div>
      </div>
      <div class="col-4">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Create a New Category</h5>
            <div
              class="card-body d-flex justify-content-between align-items-center"
            >
              <input
                type="text"
                v-model="newCategory"
                class="form-control"
                name="newCategory"
              />
              <div
                href="/admin/add_category"
                type="button"
                class="btn btn-primary"
                @click.prevent="addCategory"
              >
                Add category
              </div>
            </div>
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
            <div
              @click="deleteCategory(category.categoryID)"
              class="btn btn-darkgreen"
            >
              &#10006;
            </div>
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
import Admin_navbar from "@/components/Admin_navbar.vue";

export default {
  name: "AdminDashboard",
  components: {
    Admin_navbar,
  },
  data() {
    return {
      categories: [],
      token: sessionStorage.getItem("accessToken"),
      newCategory: "",
    };
  },
  mounted() {
    this.getIems();
    console.log(this.token);
  },
  methods: {
    addCategory() {
      if (!this.newCategory.trim()) {
        alert("Please enter a category name.");
        return;
      }
      axios
        .post(
          "http://localhost:5000/manager/categories/add_category",
          {
            category_name: this.newCategory.trim(),
          },
          {
            mode: "no-cors",
            headers: {
              Authorization: "Bearer " + this.token,
            },
          }
        )
        .then((response) => {
          console.log("Category added successfully:", response.data);
          alert("Category added successfully!");
        });
    },
    deleteCategory(categoryID) {
      if (confirm(`Are you sure you want to delete this category?`)) {
        console.log(categoryID);
        axios
          .post(
            "http://localhost:5000/manager/categories/delete_category",
            {
              categoryID: categoryID,
            },
            {
              mode: "no-cors",
              headers: {
                Authorization: "Bearer " + this.token,
              },
            }
          )
          .then((response) => {
            console.log("Category deleted successfully:", response.data);
            alert("Category deleted successfully!");
            window.location.reload();
          });
      }
    },
    getIems() {
      console.log(this.is_manager);
      axios
        .get("http://localhost:5000/api/manager/dashboard", {
          mode: "no-cors",
          headers: {
            Authorization: "Bearer " + this.token,
          },
          params: {
            is_manager: false,
          },
        })
        .then((response) => {
          if (response.error) {
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
      // Redirect to edit product page
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
                  is_manager: false,
                },
                mode: "no-cors",
                headers: {
                  Authorization: "Bearer " + this.token,
                },
              }
            )
            .then((response) => {
              if (!response.success) {
                alert(response.error);
              } else {
                window.location.reload();
                alert(
                  `Product '${product.product_name}' deleted successfully!`
                );
              }
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
