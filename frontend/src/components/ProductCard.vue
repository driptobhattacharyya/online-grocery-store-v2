<template>
  <div class="col">
    <div class="card">
      <div class="card-body">
        <h3 class="card-title">{{ product[1] }}</h3>
        <p class="card-text">Manufacture Date: {{ product[2] }}</p>
        <p class="card-text">Expiry Date: {{ product[3] }}</p>
        <p v-if="product[11]!=0 " class="card-text">Stock: {{ product[11] }} {{ product[8] }}s</p>
        <p v-if="product[11]==0 " class="card-text" style="background-color:Tomato;"> Out of Stock </p>
        
        <div v-if="product[11]!=0">
          
          <form method="POST" v-if="signed ">
            <div class="input-group mb-3">
              <span class="input-group-text">₹</span>
              <span class="input-group-text">{{ product[4] }}/{{ product[8] }}</span>
              <input
                type="number"
                class="form-control"
                placeholder="Amount"
                name="count"
                v-model="count"
              />
              <button
                class="btn btn-outline-secondary btn-custom"
                type="submit"
                id="button-addon2"
                name="product"
                :value="product[0]"
                @click.prevent="addToCart"
              >
                Add to Cart
              </button>
            </div>
          </form> 
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  props: {
    product: Object,
    signed: Boolean,
  },
  data() {
    return {
      count: 0,
    };
  },
  methods: {
    async addToCart() {
      const quantity = Number(this.count);
      if (!Number.isInteger(quantity) || quantity <= 0) {
        alert("Please enter a positive whole number");
        return;
      }
      try {
        const response = await axios.post(
          "/api/add_to_cart",
          { product_id: this.product[0], quantity },
          { headers: { Authorization: "Bearer " + sessionStorage.getItem("accessToken") } }
        );
        alert(response.data.success);
      } catch (error) {
        alert(error?.response?.data?.error || "Could not add the product to your cart.");
      }
    },
  },
};
</script>

