<template>
  <div>
    <Navbar :user="name" :signed="true" />
    <div class="container py-4 text-start">
      <h1>Wishlist</h1>
      <p v-if="!items.length">Nothing saved yet. Tap the heart on a product.</p>
      <div class="row row-cols-1 row-cols-md-3 g-3">
        <div class="col" v-for="item in items" :key="item.productID">
          <div class="card h-100">
            <div class="card-body">
              <h3>
                <router-link :to="`/products/${item.productID}`">{{ item.name }}</router-link>
              </h3>
              <p>₹{{ item.price }} / {{ item.unit }}</p>
              <p v-if="item.quantity === 0">Out of stock</p>
              <button class="btn btn-success me-2" :disabled="item.quantity === 0" @click="move(item)">
                Move to cart
              </button>
              <button class="btn btn-outline-secondary" @click="remove(item)">Remove</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Navbar from "@/components/Navbar.vue";

export default {
  components: { Navbar },
  data() {
    return { items: [], name: sessionStorage.getItem("name") || "" };
  },
  mounted() {
    this.load();
  },
  methods: {
    load() {
      axios.get("/api/wishlist").then((response) => {
        this.items = response.data.wishlist;
      });
    },
    move(item) {
      axios
        .post(`/api/wishlist/${item.productID}/move-to-cart`, { quantity: 1 })
        .then(() => this.load())
        .catch((error) => alert(error.response?.data?.error || "Could not move that item."));
    },
    remove(item) {
      axios.delete(`/api/wishlist/${item.productID}`).then(() => this.load());
    },
  },
};
</script>
