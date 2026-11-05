<template>
  <div class="container low-stock">
    <div class="d-flex justify-content-between align-items-center">
      <h2>Low stock</h2>
      <form class="d-flex gap-2" @submit.prevent="save">
        <label class="form-label mb-0 align-self-center">Threshold</label>
        <input class="form-control" type="number" min="0" v-model.number="threshold" />
        <button class="btn btn-primary" type="submit">Save</button>
      </form>
    </div>
    <p v-if="!items.length">Every product is above the threshold.</p>
    <table v-else class="table">
      <thead>
        <tr>
          <th>Product</th>
          <th>Category</th>
          <th>Left</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.productID">
          <td>{{ item.name }}</td>
          <td>{{ item.category_name }}</td>
          <td>{{ item.quantity }} {{ item.unit }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from "axios";

export default {
  props: {
    items: { type: Array, default: () => [] },
    initialThreshold: { type: Number, default: 10 },
  },
  data() {
    return { threshold: this.initialThreshold };
  },
  watch: {
    initialThreshold(value) {
      this.threshold = value;
    },
  },
  methods: {
    save() {
      axios
        .put("/api/manager/low-stock-threshold", { threshold: this.threshold })
        .then((response) => {
          this.$emit("updated", response.data);
        })
        .catch((error) => {
          alert(error.response?.data?.error || "Could not save the threshold.");
        });
    },
  },
};
</script>

<style scoped>
.low-stock {
  text-align: left;
  margin-top: 24px;
}
</style>
