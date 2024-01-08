<template>
  <Admin_navbar />
  <div class="container">
    <h2 class="mb-4">Pending Manager Requests</h2>
    <div v-if="requests.length === 0"> No manager requests currently </div>
    <div v-for="user in requests" :key="user.id">
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
export default {
  components: {
    Admin_navbar,
  },
  data() {
    return {
      requests: [],
      signed: false,
      user: "",
      manager_status: "",
      token: sessionStorage.getItem("accessToken"),
    };
  },
  mounted() {
    axios
      .get("http://localhost:5000/api/admin/manager_requests", {
        mode: "no-cors",
        headers: {
          Authorization: "Bearer " + this.token,
        },
      })
      .then((res) => {
        this.requests = res.data.manager_requests;
        console.log(res.data);
      })
      .catch((err) => {
        console.log(err);
      });
  },
  methods: {
    async accept_manager(email) {
      try {
        // get confirmation
        if (
          confirm("Are you sure you want to make this user a store manager?")
        ) {
          axios
            .post(
              "http://localhost:5000/api/admin/accept_manager",
              {
                email: email,
              },
              {
                mode: "no-cors",
                headers: {
                  Authorization: "Bearer " + this.token,
                },
              }
            )
            .then((response) => {
              console.log(response.data);
              alert("Manager request accepted");
              window.location.reload();
            })
            .catch((error) => {
              alert(error);
            });
        }
      } catch (error) {
        alert(error);
      }
    },
    async reject_manager(email) {
      try {
        if (
          confirm(
            "Are you sure you want to reject this user from being a store manager?"
          )
        ) {
          axios
            .post(
              "http://localhost:5000/api/admin/reject_manager",
              {
                email: email,
              },
              {
                mode: "no-cors",
                headers: {
                  Authorization: "Bearer " + this.token,
                },
              }
            )
            .then((response) => {
              console.log(response.data);
              alert("Manager request rejected");
              window.location.reload();
            })
            .catch((error) => {
              alert(error);
            });
        }
      } catch (error) {
        alert(error);
      }
    },
  },
};
</script>
