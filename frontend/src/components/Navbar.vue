<template>
  <nav class="navbar navbar-expand-lg">
    <div class="container-fluid">
      <a class="navbar-brand" href="#">Welcome {{ user }}</a>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <a
              href="#"
              class="nav-link active"
              aria-current="page"
              @click="goHome"
              >Home</a
            >
          </li>
          <li class="nav-item dropdown" v-if="path == '/'">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              id="categoriesDropdown"
              role="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Categories
            </a>
            <ul class="dropdown-menu" aria-labelledby="categoriesDropdown">
              <div v-for="category in categories">
                <li>
                  <div
                    class="dropdown-item"
                    href="#"
                    @click="category_products(category[0])"
                  >
                    {{ category[1] }}
                  </div>
                </li>
              </div>
            </ul>
          </li>
          <li class="nav-item" v-if="!signed">
            <a class="nav-link" href="/signup">Register</a>
          </li>
          <li class="nav-item" v-if="!signed">
            <a class="nav-link" href="/login">Login</a>
          </li>
          <li class="nav-item" v-if="signed">
            <a class="nav-link active" aria-current="page" href="/dashboard"
              >Dashboard</a
            >
          </li>
          <li class="nav-item" v-if="signed">
            <a class="nav-link active" aria-current="page" href="/shopping_cart"
              >Cart</a
            >
          </li>

          <li class="nav-item" v-if="signed">
            <a class="nav-link" href="#" @click="logout">Logout</a>
          </li>
          
          <li class="nav-item" v-if="is_manager">
            <a class="nav-link" href="/admin/dashboard" >Manager</a>
          </li>

          <li class="nav-item dropdown" v-if="path == '/'">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              id="searchDropdown"
              role="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Search
            </a>
            <div
              class="dropdown-menu search-dropdown dropdown-menu-end p-2"
              aria-labelledby="searchDropdown"
            >
              <form @submit.prevent="search" class="p-3" >
                <div class="mb-3" >
                  <label for="searchInput" class="form-label">Search</label>
                  <input
                    ref="searchInput"
                    id="searchInput"
                    class="form-control"
                    type="search"
                    placeholder="Search here"
                    aria-label="Search"
                    name="search_query"
                  />
                </div>

                <div class="mb-3">
                  <label for="minPrice" class="form-label">Min Price</label>
                  <input
                    ref="minPrice"
                    type="number"
                    step="0.01"
                    v-model="search_filters.minPrice"
                    class="form-control"
                    placeholder="Min Price"
                    name="min_price"
                  />
                </div>

                <div class="mb-3">
                  <label for="maxPrice" class="form-label">Max Price</label>
                  <input
                    type="number"
                    step="0.01"
                    v-model="search_filters.maxPrice"
                    class="form-control"
                    placeholder="Max Price"
                    name="max_price"
                  />
                </div>
                <div class="spacer"></div>
                <div class="d-flex mt-2 mt-md-0 date-filters">
                  <div class="me-2">
                    <span class="mb-1">Min Manufacture Date</span>
                    <input
                      type="date"
                      class="form-control"
                      v-model="search_filters.min_manufacture_date"
                      name="min_manufacture_date"
                    />
                  </div>
                  <div>
                    <span class="mb-1">Max Manufacture Date</span>
                    <input
                      type="date"
                      v-model="search_filters.max_manufacture_date"
                      class="form-control"
                      name="max_manufacture_date"
                    />
                  </div>
                </div>
                <div class="spacer"></div>
                <div class="d-flex mt-2 mt-md-0 date-filters">
                  <div class="me-2">
                    <span class="mb-1">Min Expiry Date</span>
                    <input
                      type="date"
                      v-model="search_filters.min_expiry_date"
                      class="form-control"
                      name="min_expiry_date"
                    />
                  </div>
                  <div>
                    <span class="mb-1">Max Expiry Date</span>
                    <input
                      type="date"
                      class="form-control"
                      v-model="search_filters.max_manufacture_date"
                      name="max_expiry_date"
                    />
                  </div>
                </div>
                <div class="mb-3 form-check form-switch">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    id="excludeOutOfStock"
                    v-model="search_filters.exclude_OOS"
                    name="exclude_out_of_stock"
                  />
                  <label class="form-check-label" for="excludeOutOfStock">
                    Exclude Out of Stock
                  </label>
                </div>

                <button class="btn btn-outline-success" type="submit">
                  Search
                </button>
              </form>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
import axios from "axios";
export default {
  props: {
    signed: Boolean,
    user: String,
  },
  data() {
    return {
      data: [],
      categories: [],
      is_manager: false,
      search_filters:{
        minPrice:0,
        maxPrice: 0,
        min_manufacture_date: 0,
        max_manufacture_date: 0,
        min_expiry_date:  "",
        max_expiry_date: "",
        exclude_OOS: false
      }
    };
  },
  mounted() {
    this.getCategories();
  },
  computed: {
    path() {
      return this.$route.path;
    },
  },
  methods: {
    async getCategories() {
      axios
        .get("http://localhost:5000/api/getCategories")
        .then((response) => {
          this.categories = response.data;
          console.log(this.categories);
        })
        .catch((error) => {
          alert("Error fetching data:", error);
        });
    },
    category_products(categoryID) {
      console.log("Checking a particular category");
      // if (!this.data.length) {
      axios
        .get(`http://localhost:5000/api/category/${categoryID}`)
        .then((response) => {
          this.data = response.data;
          console.log(this.data);
          // send_data_to_parent();
          if (this.$route.path === "/") {
            this.$emit("ChildEvent", this.data);
          } else {
            this.$router.push("/");
            console.log("Hi");
            this.$emit("ChildEvent", this.data);
          }
        })
        .catch((error) => {
          console.error("Error fetching data:", error);
        });
      // }
    },
    search() {
      try {
        const searchQuery = this.$refs.searchInput.value;
        console.log(searchQuery)
        
        
        axios.post("http://localhost:5000/api/search", {
          search_query: searchQuery,
          min_price: this.search_filters.minPrice,
          max_price: this.search_filters.maxPrice,
          min_manufacture_date: this.search_filters.min_manufacture_date,
          max_manufacture_date: this.search_filters.max_manufacture_date,
          min_expiry_date: this.search_filters.min_expiry_date,
          max_expiry_date: this.search_filters.max_expiry_date,
          exclude_out_of_stock: this.search_filters.exclude_OOS
        })
        .then((response) =>{
          if(response.data.products){
            this.$emit("ChildEvent", response.data.products);
          }
          else if(response.data.products_in_category){
            this.$emit("ChildEvent", response.data.products_in_category);
          }
          else if(response.data.no_results){
            alert("No results found");
          }
          
        })
        .catch((error) => {
          console.error("Error fetching data:", error);
        });
      } catch (error) {
        console.error("Error performing search:", error);
      }
    },
    goHome() {
      if (this.$route.path === "/") {
        window.location.reload();
      } else {
        this.$router.push("/");
      }
    },
    logout() {
      sessionStorage.removeItem("accessToken");
      sessionStorage.removeItem("signed");
      sessionStorage.removeItem("name");
      alert("Logged out successfully");
      if (this.$route.path === "/") {
        window.location.reload();
      } else {
        this.$router.push("/");
      }
    },
  },
};
</script>
