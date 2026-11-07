<template>
  <Admin_navbar />
  <div class="container">
    <h2 class="mb-4">Pending Manager Requests</h2>
    <div v-if="requests.length === 0"> No manager requests currently </div>
    <div v-for="user in requests" :key="user.email">
      <div class="col-md-6 mx-auto">
        <div class="card user-info-card">
          <div class="card-body">
            <h4 class="card-title">{{ user.name }}</h4>
            <p class="card-text"><strong>Email:</strong> {{ user.email }}</p>
            <p class="card-text">
              <strong>Phone No:</strong> {{ user.phone_no }}
            </p>
            <p class="card-text">
              <strong>Address:</strong> {{ user.address }}
            </p>
          </div>
          <div class="card-footer">
            <div
              class="btn btn-primary btn-sm"
              @click="accept_manager(user.email)"
            >
              <strong>Accept</strong>
            </div>
            <div
              class="btn btn-darkgreen btn-sm"
              @click="reject_manager(user.email)"
            >
              <strong>Reject</strong>
            </div>
          </div>
        </div>
      </div>
      <br />
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Admin_navbar from "@/components/Admin_navbar.vue";
import "@/assets/style_manager.css";

function errorMessage(error, fallback) {
  return error?.response?.data?.error || fallback;
}

export default {
  components: {
    Admin_navbar,
  },
  data() {
    return {
      requests: [],
      token: sessionStorage.getItem("accessToken"),
    };
  },
  mounted() {
    this.loadRequests();
  },
  methods: {
    authHeaders() {
      return { headers: { Authorization: "Bearer " + this.token } };
    },
    async loadRequests() {
      try {
        const response = await axios.get("/api/admin/manager_requests", this.authHeaders());
        this.requests = response.data.manager_requests;
      } catch (error) {
        console.error("Error loading manager requests:", error);
        alert(errorMessage(error, "Could not load manager requests."));
      }
    },
    async decide(endpoint, email, doneMessage) {
      try {
        await axios.post(endpoint, { email }, this.authHeaders());
        alert(doneMessage);
        this.loadRequests();
      } catch (error) {
        alert(errorMessage(error, "Could not update the request."));
      }
    },
    accept_manager(email) {
      if (confirm("Are you sure you want to make this user a store manager?")) {
        this.decide("/api/admin/accept_manager", email, "Manager request accepted");
      }
    },
    reject_manager(email) {
      if (confirm("Are you sure you want to reject this user from being a store manager?")) {
        this.decide("/api/admin/reject_manager", email, "Manager request rejected");
      }
    },
  },
};
</script>
