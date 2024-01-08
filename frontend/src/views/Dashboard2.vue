<template>
  <div>
    <Navbar :user="name" :signed="signed" @ChildEvent="handleChildEvent" />
    <div class="container">
      <div class="row">        
        <div class="col-md-6">
          <div class="card user-info-card">
            <div class="card-body">
              <h4 class="card-title">User Information</h4>
              <p class="card-text"><strong>Name:</strong> {{ user.name }}</p>
              <p class="card-text"><strong>Email:</strong> {{ user.email }}</p>
              <p class="card-text"><strong>Phone No:</strong> {{ user.phone_no }}</p>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card user-info-card">
            <div class="card-body">
              <h4 class="card-title">Manager Status</h4>
              <p class="card-text">{{ manager_status }}</p>            
              <div class="btn btn-primary btn-sm" v-if=" manager_status =='Not Applied'" @click="apply_manager"> <strong>Apply Now</strong></div>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-8 mx-auto">
        <h1 class="text-center">User Order History</h1>

        <div v-for="order in orders" :key="order.id" class="order-card card mb-3">
          <div class="card-body">
            <p class="order-date">{{ order.order_date }}</p>
            <ul class="order-items list-group">
              <li v-for="item in order.items" :key="item.product_id" class="order-item list-group-item">
                {{ item.quantity }} x {{ item.product_name }}
              </li>
            </ul>
            <p class="order-total mt-3">Total: ₹{{ order.total_price }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Navbar from "@/components/Navbar.vue";
import "@/assets/style.css";

export default {
  components:{
    Navbar,
  },
  data() {
    return {
      user: {},
      orders: [],
      signed: false,
      user: "",
      manager_status: ""
    };
  },
  mounted() {
    this.fetch_user_dashboard();
    this.signed = sessionStorage.getItem("signed");
    this.name = sessionStorage.getItem("name");
  },
  methods:{
    async fetch_user_dashboard() {
      try {
        const token = sessionStorage.getItem("accessToken");
        console.log(token);
        axios
          .get("http://localhost:5000/api/dashboard", {
            mode: "no-cors",
            headers: {
              Authorization: "Bearer " + token,
            },
          })
          .then((response) => {
            this.received_data = response.data;
            console.log(this.received_data);
            this.user = this.received_data.user_info;
            this.orders = this.received_data.user_orders;
            this.manager_status = this.received_data.manager_status;
          });
      } catch (error) {
        console.error("Error:", error);
      }
    },

    async apply_manager() {
      try {
        const token = sessionStorage.getItem("accessToken");
        console.log(token);
        axios
          .get("http://localhost:5000/api/apply_manager", {
            mode: "no-cors",
            headers: {
              Authorization: "Bearer " + token,
            },
          })
          .then((response) => {
            console.log(this.received_data);
            if (response.data.success){
              alert("Successfully applied");
              window.location.reload();
            } else {
              alert(response.data.error);
            }
          });
      } catch (error) {
        console.error("Error:", error);
      }
    },
  }
};
</script>

<style scoped>
/* Add your custom styles here */
.container {
  margin-top: 30px;
}

.card-space {
  margin-bottom: 20px;
}

.card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.305);
}

.user-info-card {
  margin-bottom: 30px;
}

.order-card {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.order-date {
  font-size: 18px;
  font-weight: bold;
}

.order-items {
  margin-bottom: 10px;
}

.order-item {
  font-size: 16px;
}

.order-total {
  font-size: 18px;
  font-weight: bold;
  color: #28a745; /* Green color for total price */
}
</style>