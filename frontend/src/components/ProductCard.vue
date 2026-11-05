<template>
  <div class="col">
    <div class="card h-100">
      <div class="card-body">
        <h3 class="card-title">
          <router-link :to="`/products/${product.productID}`">{{ product.name }}</router-link>
        </h3>
        <p class="card-text">{{ stars }} {{ product.average_rating || 0 }} ({{ product.review_count || 0 }})</p>
        <p class="card-text">{{ product.description }}</p>
        <p class="card-text">Manufacture: {{ product.manufacture_date }}</p>
        <p class="card-text">Expiry: {{ product.expiry_date }}</p>
        <p v-if="product.quantity > 0" class="card-text">Stock: {{ product.quantity }} {{ product.unit }}</p>
        <p v-else class="card-text out">Out of stock</p>
        <form v-if="product.quantity > 0 && signed" @submit.prevent="addToCart">
          <div class="input-group mb-3">
            <span class="input-group-text">₹{{ product.price }}/{{ product.unit }}</span>
            <input type="number" min="1" class="form-control" v-model.number="count" />
            <button class="btn btn-outline-secondary btn-custom" type="submit">Add to Cart</button>
          </div>
        </form>
        <button v-if="signed" class="btn btn-link" type="button" @click="save">Save to wishlist</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  props: {
    product: { type: Object, required: true },
    signed: { type: Boolean, default: false },
  },
  data() {
    return { count: 1 };
  },
  computed: {
    stars() {
      const filled = Math.round(this.product.average_rating || 0);
      return "★★★★★".slice(0, filled) + "☆☆☆☆☆".slice(0, 5 - filled);
    },
  },
  methods: {
    addToCart() {
      if (!this.count || this.count <= 0) {
        alert("Please enter a positive value");
        return;
      }
      axios
        .post("/api/add_to_cart", { product_id: this.product.productID, quantity: this.count })
        .then((response) => alert(response.data.success || response.data.error))
        .catch((error) => alert(error.response?.data?.error || "Could not add to cart."));
    },
    save() {
      axios
        .post("/api/wishlist", { product_id: this.product.productID })
        .then((response) => alert(response.data.success))
        .catch((error) => alert(error.response?.data?.error || "Could not save."));
    },
  },
};
</script>

<style scoped>
.out {
  background-color: tomato;
}
</style>
