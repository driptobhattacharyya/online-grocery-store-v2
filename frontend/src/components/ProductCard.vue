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
import axios from 'axios';

export default {
  props: {
    product: Object,
    signed: Boolean,
  },
  data() {
    return {
      count: 0
    };
  },
  methods: {
    addToCart() {
      let product_id = this.product[0];
      let count = this.count;
      if(count <= 0){
        alert("Please enter a positive value")
      } else {
        const token = sessionStorage.getItem("accessToken");
        console.log(token);
        axios
          .post("http://localhost:5000/api/add_to_cart", {
            "product_id": product_id,
            "quantity": count,
          },{
            mode: 'no-cors',
            headers: {
              'Authorization': "Bearer "+token
            }
          })
          .then((response) => {
            console.log(response.data);
            if (response.data.success){
              alert(response.data.success)
            } else {
              alert(response.data.error)
            }
          })
          .catch((error) => {
            // Handle login error
            console.error(error.data.error);
          });
      }
    }
  }
};
</script>

