<template>
  <div>
    <component :is="navbar" />
    <div class="container py-4 text-start">
      <h1>Store summary</h1>
      <p v-if="windowLabel">Units sold from {{ windowLabel }}.</p>
      <div class="row">
        <div class="col-md-7">
          <h2>Sales, last 7 days</h2>
          <p v-if="!bar.length">No sales in this window yet.</p>
          <canvas ref="barCanvas"></canvas>
        </div>
        <div class="col-md-5">
          <h2>Products by category</h2>
          <canvas ref="pieCanvas"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Chart from "chart.js/auto";
import Admin_navbar from "@/components/Admin_navbar.vue";
import Manager_navbar from "@/components/Manager_navbar.vue";

export default {
  components: { Admin_navbar, Manager_navbar },
  data() {
    return { bar: [], pie: [], windowLabel: "", charts: [] };
  },
  computed: {
    navbar() {
      return sessionStorage.getItem("role") === "admin" ? "Admin_navbar" : "Manager_navbar";
    },
  },
  mounted() {
    axios.get("/api/manager/summary").then((response) => {
      this.bar = response.data.bar;
      this.pie = response.data.pie;
      this.windowLabel = `${response.data.window.start} to ${response.data.window.end}`;
      this.$nextTick(() => this.draw());
    });
  },
  beforeUnmount() {
    this.charts.forEach((chart) => chart.destroy());
  },
  methods: {
    draw() {
      if (this.bar.length) {
        this.charts.push(
          new Chart(this.$refs.barCanvas, {
            type: "bar",
            data: {
              labels: this.bar.map((row) => row.product),
              datasets: [
                {
                  label: "Units sold",
                  data: this.bar.map((row) => row.quantity),
                  backgroundColor: "#2e8b57",
                },
              ],
            },
            options: { responsive: true, plugins: { legend: { display: false } } },
          })
        );
      }
      this.charts.push(
        new Chart(this.$refs.pieCanvas, {
          type: "pie",
          data: {
            labels: this.pie.map((row) => row.category),
            datasets: [
              {
                data: this.pie.map((row) => row.count),
                backgroundColor: ["#2e8b57", "#f4a261", "#e76f51", "#264653", "#e9c46a", "#8ab17d", "#6d597a"],
              },
            ],
          },
        })
      );
    },
  },
};
</script>
