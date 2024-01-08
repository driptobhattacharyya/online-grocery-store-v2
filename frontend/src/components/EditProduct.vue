<template>
  <div class="container py-4 py-xl-5 mx-auto col-xl-3">
    <h1>Edit Product</h1>
    <br />
    <form @submit.prevent="editProduct">
      <div class="mb-3">
        <label class="form-label">Name</label>
        <input
          type="text"
          class="form-control"
          name="name"
          aria-describedby="emailHelp"
          v-model="newProduct.name"
          required
        />
      </div>
      <div class="mb-3">
        <label class="form-label">Category:</label>
        <select class="form-control" v-model="newProduct.category" required>
          <option value="" disabled>Select a category</option>

          <option
            v-for="category in categories"
            :key="category.id"
            :value="category[1]"
          >
            {{ category[1] }}
          </option>
        </select>
      </div>
      <div class="mb-3">
        <label class="form-label">Stock</label>
        <input
          v-model="newProduct.quantity"
          type="number"
          class="form-control"
          name="quantity"
          required
        />
      </div>
      <div class="mb-3">
        <label class="form-label">Price per unit</label>
        <input
          type="number"
          v-model="newProduct.price"
          step="0.01"
          class="form-control"
          name="price"
          required
        />
      </div>
      <div class="mb-3">
        <label class="form-label">Unit</label>
        <input
          type="text"
          v-model="newProduct.unit"
          class="form-control"
          name="unit"
          required
        />
      </div>
      <div class="mb-3">
        <label class="form-label">Manufacture Date</label>
        <input
          type="date"
          class="form-control"
          name="manufacture_date"
          v-model="newProduct.manufacture_date"
          required
        />
      </div>
      <div class="mb-3">
        <label class="form-label">Expiry Date</label>
        <input
          type="date"
          class="form-control"
          v-model="newProduct.expiry_date"
          name="expiry_date"
          required
        />
      </div>
      <button type="submit" class="btn btn-primary">Update Product</button>
    </form>
  </div>
</template>

<script>
import axios from "axios";
import "@/assets/style_manager.css";
export default {
  name: "EditProduct",
  props: {
    product: Object,
  },
  data() {
    return {
      product_id: null,
      categories: [],
      newProduct: {
        name: sessionStorage.getItem("productName"),
        category: "",
        quantity: sessionStorage.getItem("productQuantity"),
        price: sessionStorage.getItem("productPrice"),
        unit: sessionStorage.getItem("productUnit"),
        manufacture_date: sessionStorage.getItem("productMnfdate"),
        expiry_date: sessionStorage.getItem("productExpdate"),
      },
      token: sessionStorage.getItem("accessToken"),
      is_manager: sessionStorage.getItem("is_manager")
    };
  },
  mounted() {
    this.getCategories();
  },
  created() {
    console.log("Received product parameter:", this.$route.params.product_id);
    // this.getProduct(this.product_id)
    this.product_id = this.$route.params.product_id;
  },
  methods: {
    async getCategories() {
      axios
        .get("http://localhost:5000/api/getCategories")
        .then((response) => {
          this.categories = response.data;
          console.log(this.categories);
        })
        .catch((error) => {
          alert("Error fetching data:", error);
        });
    },
    editProduct() {
      // Validate required fields
      if (
        !this.newProduct.name ||
        !this.newProduct.category ||
        !this.newProduct.quantity ||
        !this.newProduct.price ||
        !this.newProduct.unit ||
        !this.newProduct.manufacture_date ||
        !this.newProduct.expiry_date
      ) {
        alert("Please fill in all required fields!");
        return;
      }
      console.log(this.newProduct);
      console.log(this.product_id);
      
      axios
        .post(
          "http://localhost:5000/api/manager/edit_product",
          {
            product_id: this.product_id,
            product_name: this.newProduct.name,
            category: this.newProduct.category,
            quantity: this.newProduct.quantity,
            price: this.newProduct.price,
            unit: this.newProduct.unit,
            manufacture_date: this.newProduct.manufacture_date,
            expiry_date: this.newProduct.expiry_date,
            is_manager: this.is_manager,
          },
          {
            mode: "no-cors",
            headers: {
              Authorization: "Bearer " + this.token,
            },
          }
        )
        .then(() => {
          // Handle success message and redirect or update app state
          if (true) {
            alert("Product updated successfully!");
            sessionStorage.removeItem("productName");
            sessionStorage.removeItem("productQuantity");
            sessionStorage.removeItem("productUnit");
            sessionStorage.removeItem("productPrice");
            sessionStorage.removeItem("productMnfdate");
            sessionStorage.removeItem("productExpdate");
            console.log(sessionStorage)
            if (this.is_manager){
                    this.$router.push("/StoreManager/dashboard");
                } else {
                  this.$router.push("/admin/dashboard");
            }
            // Reset form
            this.newProduct = {
              name: "",
              category: "",
              quantity: 0,
              price: 0,
              unit: "",
              manufacture_date: "",
              expiry_date: "",
            };
          } else {
            alert("Server error updating product: " + response.data.error);
          }
        })
        .catch((error) => {
          console.error(error);
          alert("Error updating product: " + error.message);
        });
    },
  },
};
</script>
