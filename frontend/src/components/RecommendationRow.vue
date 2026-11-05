<template>
  <section v-if="items.length" class="recommendations">
    <h2>{{ title }}</h2>
    <div class="row row-cols-1 row-cols-md-3 g-3">
      <div class="col" v-for="item in items" :key="item.productID">
        <div class="card h-100">
          <div class="card-body">
            <h3 class="card-title">
              <router-link :to="`/products/${item.productID}`">{{ item.name }}</router-link>
            </h3>
            <p class="card-text">₹{{ item.price }} / {{ item.unit }}</p>
            <p class="reason">{{ item.reason }}</p>
            <button class="btn btn-outline-success btn-sm" @click="add(item)" :disabled="!signed">
              Add to cart
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import axios from "axios";

export default {
  props: {
    title: { type: String, default: "You might also like" },
    items: { type: Array, default: () => [] },
    signed: { type: Boolean, default: false },
  },
  methods: {
    add(item) {
      if (!this.signed) {
        this.$router.push("/login");
        return;
      }
      axios
        .post("/api/add_to_cart", { product_id: item.productID, quantity: 1 })
        .then((response) => {
          alert(response.data.success || "Added");
          this.$emit("added");
        })
        .catch((error) => {
          alert(error.response?.data?.error || "Could not add that item.");
        });
    },
  },
};
</script>

<style scoped>
.recommendations {
  margin: 28px auto;
  max-width: 1100px;
  text-align: left;
}
.reason {
  color: #1e7a46;
  font-size: 0.95rem;
}
</style>
