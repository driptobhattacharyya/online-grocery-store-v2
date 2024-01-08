<template>
    <Admin_navbar />
</template>

<script>
import Admin_navbar from "../components/Admin_navbar.vue";
export default {
    components: {
        Admin_navbar,
    },
    data() {
        return {
            requests: [],
        };
    },
    mounted() {
        this.getRequests();
    },
    methods: {
        getRequests() {
            axios
                .get("http://localhost:8000/api/manager-requests")
                .then((response) => {
                    this.requests = response.data;
                })
                .catch((error) => {
                    console.log(error);
                });
        },
        acceptRequest(id) {
            axios
                .post("http://localhost:8000/api/accept-request", {
                    id: id,
                })
                .then((response) => {
                    this.getRequests();
                })
                .catch((error) => {
                    console.log(error);
                });
        },
        rejectRequest(id) {
            axios
                .post("http://localhost:8000/api/reject-request", {
                    id: id,
                })
                .then((response) => {
                    this.getRequests();
                })
                .catch((error) => {
                    console.log(error);
                });
        },
    },
};
</script>