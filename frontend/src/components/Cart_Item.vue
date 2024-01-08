<template>
  <div class="card mb-3">
    <div class="row g-0">
      <div class="col-md-8">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center">
            <h5 class="card-title">{{ cartItem.name }}</h5>
            <a @click="deleteItem" class="btn btn-sm delete-button">&#10006;</a>
          </div>
          <p class="card-text">Price: ₹{{ cartItem.price }}</p>
          <div class="d-flex align-items-center justify-content-center mb-3">
            <p class="card-text me-2">Quantity:</p>
            <form @submit.prevent="updateItem">
              <input
                type="number"
                class="form-control me-2"
                style="max-width: 70px"
                v-model="quantity"
              />
              <button type="submit" class="btn btn-primary btn-sm">
                Update
              </button>
            </form>
          </div>
          <p class="card-text" style="font-weight: bold">
            Total: ₹{{ cartItem.price * cartItem.quantity }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import "@/assets/style.css";
import axios from "axios";
export default {
  props: {
    cartItem: Object,
    token: String,
  },
  data() {
    return {
      quantity: this.cartItem.quantity,
    };
  },
  methods: {
    updateItem() {
      if (this.quantity <= 0){
        alert("Please enter a valid quantity")
      } else{
        try {
          console.log(this.cartItem.productID, this.quantity);
          const response = axios.post(
            "http://127.0.0.1:5000/api/shopping_cart/update_product",
            {
              product_id: this.cartItem.productID,
              quantity: this.quantity,
            },
            {
              mode: "no-cors",
              headers: {
                Authorization: "Bearer " + this.token,
              },
            }
          );
          alert("Quantity updated")
        } catch (error) {
          console.error("Error:", error);
        }
      }
    },
    deleteItem() {
      if (confirm("Are you sure you want to delete this item  from your cart")){
        try {
          axios.post(
            "http://127.0.0.1:5000/api/shopping_cart/delete_product",
            {
              "product_id": this.cartItem.productID,
            },
            {
              mode: "no-cors",
              headers: {
                Authorization: "Bearer " + this.token,
              },
            }
          );
          alert("Deleted from cart")
          window.location.reload()
        } catch (error) {
          console.error("Error:", error);
        }
      }
    },
  },
};
</script>

<style scoped>
/* Add your custom styles here */
.btn-outline-success {
  color: #fff;
  background-color: #27ae60;
  border-color: #27ae60;
}
.card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.305);
}
.add-gap {
  margin-top: 20px;
}
.cart-total {
  font-size: 24px;
  margin-top: 20px;
  text-align: center;
}
.checkout-btn {
  font-size: 18px;
  display: block;
  margin: 20px auto;
}
.delete-button {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 24px;
  color: #dc3545;
  cursor: pointer;
  transition: color 0.3s;
}
.delete-button:hover {
  color: #c82333;
}
.card-title {
  font-size: 35px;
  margin-bottom: 10px;
}
.card-text {
  font-size: 20px;
  color: black;
  margin-bottom: 10px;
  text-align: center;
}
.right-pane {
  position: sticky;
  top: 20px;
  right: 20px;
  background-color: white;
  padding: 10px;
  border: 1px solid #ccc;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1;
  max-height: calc(30vh - 40px);
  overflow-y: auto;
}
</style>
