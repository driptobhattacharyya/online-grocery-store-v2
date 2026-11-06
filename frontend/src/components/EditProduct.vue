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
            :key="category[0]"
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
      <button type="submit" class="btn btn-primary" :disabled="saving">Update Product</button>
    </form>
  </div>
</template>

<script>
import axios from "axios";
import { getRole, homeFor } from "@/auth";
import "@/assets/style_manager.css";

const EMPTY_PRODUCT = {
  name: "",
  category: "",
  quantity: 0,
  price: 0,
  unit: "",
  manufacture_date: "",
  expiry_date: "",
};
const STORED_KEYS = {
  name: "productName",
  category: "productCategory",
  quantity: "productQuantity",
  price: "productPrice",
  unit: "productUnit",
  manufacture_date: "productMnfdate",
  expiry_date: "productExpdate",
};

/** Returns an error message, or "" when the form is valid. */
function validate(product) {
  const missing = ["name", "category", "unit", "manufacture_date", "expiry_date"].some(
    (field) => !String(product[field] ?? "").trim()
  );
  if (missing || product.quantity === "" || product.price === "") {
    return "Please fill in all required fields!";
  }
  const quantity = Number(product.quantity);
  if (!Number.isInteger(quantity) || quantity < 0) return "Stock must be a whole number (0 or more).";
  if (!(Number(product.price) > 0)) return "Price must be greater than zero.";
  if (product.expiry_date < product.manufacture_date) {
    return "Expiry date cannot be before the manufacture date.";
  }
  return "";
}

export default {
  name: "EditProduct",
  data() {
    return {
      product_id: this.$route.params.product_id,
      newProduct: Object.fromEntries(
        Object.entries(STORED_KEYS).map(([field, key]) => [field, sessionStorage.getItem(key) ?? EMPTY_PRODUCT[field]])
      ),
      categories: [],
      saving: false,
      token: sessionStorage.getItem("accessToken"),
    };
  },
  mounted() {
    this.getCategories();
  },
  methods: {
    async getCategories() {
      try {
        const response = await axios.get("/api/getCategories");
        this.categories = response.data;
      } catch (error) {
        alert(error?.response?.data?.error || "Could not load categories.");
      }
    },
    async editProduct() {
      const problem = validate(this.newProduct);
      if (problem) {
        alert(problem);
        return;
      }
      this.saving = true;
      try {
        await axios.post(
          "/api/manager/edit_product",
          {
            product_id: this.product_id,
            product_name: this.newProduct.name.trim(),
            category: this.newProduct.category,
            quantity: Number(this.newProduct.quantity),
            price: Number(this.newProduct.price),
            unit: this.newProduct.unit.trim(),
            manufacture_date: this.newProduct.manufacture_date,
            expiry_date: this.newProduct.expiry_date,
          },
          { headers: { Authorization: "Bearer " + this.token } }
        );
        alert("Product updated successfully!");
        Object.values(STORED_KEYS).forEach((key) => sessionStorage.removeItem(key));
        this.newProduct = { ...EMPTY_PRODUCT };
        this.$router.push(homeFor(getRole()));
      } catch (error) {
        alert(error?.response?.data?.error || "Could not update the product.");
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>
