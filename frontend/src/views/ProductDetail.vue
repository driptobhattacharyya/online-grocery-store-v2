<template>
  <div>
    <Navbar :user="name" :signed="signed" />
    <div class="container py-4 text-start" v-if="product">
      <h1>{{ product.name }}</h1>
      <p>{{ product.description }}</p>
      <p>₹{{ product.price }} / {{ product.unit }}</p>
      <p>{{ stars }} {{ product.average_rating }} ({{ product.review_count }} reviews)</p>
      <p v-if="product.quantity === 0" class="text-danger">Out of stock</p>
      <p v-else>In stock: {{ product.quantity }} {{ product.unit }}</p>
      <div class="d-flex gap-2 mb-4" v-if="signed && product.quantity > 0">
        <input class="form-control" style="max-width: 100px" type="number" min="1" v-model.number="quantity" />
        <button class="btn btn-success" @click="addToCart">Add to cart</button>
        <button class="btn btn-outline-secondary" @click="save">Wishlist</button>
      </div>
      <RecommendationRow title="Frequently bought together" :items="product.bought_together || []" :signed="signed" />
      <h2>Reviews</h2>
      <form v-if="signed" class="mb-4" @submit.prevent="review">
        <label class="form-label">Your rating</label>
        <select class="form-select mb-2" style="max-width: 160px" v-model.number="rating">
          <option :value="5">5</option>
          <option :value="4">4</option>
          <option :value="3">3</option>
          <option :value="2">2</option>
          <option :value="1">1</option>
        </select>
        <textarea class="form-control mb-2" v-model="body" placeholder="How was it?"></textarea>
        <button class="btn btn-primary" type="submit">Save review</button>
      </form>
      <article v-for="(item, index) in product.reviews" :key="index" class="mb-3">
        <strong>{{ item.author }}</strong> — {{ item.rating }}/5
        <p>{{ item.body }}</p>
      </article>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Navbar from "@/components/Navbar.vue";
import RecommendationRow from "@/components/RecommendationRow.vue";

export default {
  components: { Navbar, RecommendationRow },
  data() {
    return {
      product: null,
      quantity: 1,
      rating: 5,
      body: "",
      signed: sessionStorage.getItem("signed") === "true",
      name: sessionStorage.getItem("name") || "",
    };
  },
  computed: {
    stars() {
      const filled = Math.round(this.product?.average_rating || 0);
      return "★★★★★".slice(0, filled) + "☆☆☆☆☆".slice(0, 5 - filled);
    },
  },
  mounted() {
    this.load();
  },
  methods: {
    load() {
      axios.get(`/api/products/${this.$route.params.id}`).then((response) => {
        this.product = response.data.product;
      });
    },
    addToCart() {
      axios
        .post("/api/add_to_cart", { product_id: this.product.productID, quantity: this.quantity })
        .then((response) => alert(response.data.success))
        .catch((error) => alert(error.response?.data?.error || "Could not add to cart."));
    },
    save() {
      axios
        .post("/api/wishlist", { product_id: this.product.productID })
        .then((response) => alert(response.data.success))
        .catch((error) => alert(error.response?.data?.error || "Could not save."));
    },
    review() {
      axios
        .post(`/api/products/${this.product.productID}/reviews`, {
          rating: this.rating,
          body: this.body,
        })
        .then(() => {
          this.body = "";
          this.load();
        })
        .catch((error) => alert(error.response?.data?.error || "Could not save the review."));
    },
  },
};
</script>
