<template>
  <div>
    <Navbar :user="name" :signed="signed" />
    <div class="container py-4 text-start">
      <h1>Shopping assistant</h1>
      <p>
        Describe a meal or a shopping list. With an OpenAI key the assistant uses that model;
        otherwise it matches your words to the catalog on this machine.
      </p>
      <form @submit.prevent="ask">
        <textarea class="form-control mb-2" rows="4" v-model="message" placeholder="I want to make breakfast with milk, bread and eggs"></textarea>
        <button class="btn btn-success" type="submit">Ask</button>
      </form>
      <p class="mt-3" v-if="reply">{{ reply }} <small v-if="provider">({{ provider }})</small></p>
      <div class="row row-cols-1 row-cols-md-3 g-3">
        <div class="col" v-for="item in products" :key="item.productID">
          <div class="card h-100">
            <div class="card-body">
              <h3>{{ item.name }}</h3>
              <p>₹{{ item.price }} / {{ item.unit }}</p>
              <p>{{ item.reason }}</p>
              <button class="btn btn-outline-success btn-sm" @click="add(item)" :disabled="!signed">Add</button>
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
    return {
      message: "",
      reply: "",
      provider: "",
      products: [],
      signed: sessionStorage.getItem("signed") === "true",
      name: sessionStorage.getItem("name") || "",
    };
  },
  methods: {
    ask() {
      axios
        .post("/api/assistant", { message: this.message })
        .then((response) => {
          this.reply = response.data.reply;
          this.provider = response.data.provider;
          this.products = response.data.products;
        })
        .catch((error) => alert(error.response?.data?.error || "The assistant is unavailable."));
    },
    add(item) {
      axios
        .post("/api/add_to_cart", { product_id: item.productID, quantity: 1 })
        .then((response) => alert(response.data.success))
        .catch((error) => alert(error.response?.data?.error || "Could not add that item."));
    },
  },
};
</script>
