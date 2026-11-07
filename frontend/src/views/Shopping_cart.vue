<template>
  <div>
    <Navbar :user="name" :signed="signed" />
    <div class="container">
      <h1 class="cart-title">Your Shopping Cart</h1>
      <div class="row">
        <div class="col-9">
          <div class="row">
            <div class="add-gap"></div>
            <div
              class="col-12"
              v-for="cartItem in cartItems"
              :key="cartItem.productID"
            >
              <div class="mb-3">
                <Cart_Item
                  :cartItem="cartItem"
                  :token="token"
                  @updateCart="fetchCartItems"
                  @deleteItem="fetchCartItems"
                />
              </div>
            </div>
          </div>
        </div>
        <div class="col-3 right-pane">
          <div class="cart-total">Total: ₹{{ totalAmount.toFixed(2) }}</div>
          <div>
            <button
              type="button"
              class="btn btn-primary checkout-btn"
              :disabled="checkingOut || cartItems.length === 0"
              @click="checkout"
            >
              Checkout
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="add-gap"></div>
    <div v-if="cartItems.length === 0">
      <div class="card-body text-center">
        <h4>Your cart is empty.</h4>
        <router-link to="/" class="btn btn-primary">Continue Shopping</router-link>
      </div>
    </div>
  </div>
  <div
    class="modal fade"
    id="orderPlacedModal"
    tabindex="-1"
    aria-labelledby="orderPlacedModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="orderPlacedModalLabel">
            Order Placed Successfully
          </h5>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          Your order has been placed successfully. Thank you for shopping with
          us!
        </div>
        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Cart_Item from "@/components/Cart_Item.vue";
import Navbar from "@/components/Navbar.vue";
import "../assets/style.css";

export default {
  components: {
    Navbar,
    Cart_Item,
  },
  data() {
    return {
      cartItems: [],
      signed: false,
      name: "",
      checkingOut: false,
      token: sessionStorage.getItem("accessToken"),
    };
  },
  computed: {
    // Estimate for display only; the server computes the real total at checkout.
    totalAmount() {
      return this.cartItems.reduce((total, item) => total + item.price * item.quantity, 0);
    },
  },
  mounted() {
    this.fetchCartItems();
    this.signed = sessionStorage.getItem("signed") === "true";
    this.name = sessionStorage.getItem("name");
  },
  methods: {
    authHeaders() {
      return { headers: { Authorization: "Bearer " + this.token } };
    },
    async fetchCartItems() {
      try {
        const response = await axios.get("/api/shopping_cart", this.authHeaders());
        this.cartItems = response.data.cart;
      } catch (error) {
        console.error("Error loading cart:", error);
        alert(error?.response?.data?.error || "Could not load your cart.");
      }
    },
    async checkout() {
      this.checkingOut = true;
      try {
        const response = await axios.post("/api/shopping_cart/checkout", {}, this.authHeaders());
        sessionStorage.setItem("cartItems", JSON.stringify(response.data.cart_items));
        sessionStorage.setItem("totalAmount", response.data.totalPrice);
        sessionStorage.setItem("orderId", response.data.order_id);
        this.$router.push("/order-confirmation");
      } catch (error) {
        alert(error?.response?.data?.error || "Checkout failed. Please try again.");
        this.fetchCartItems();
      } finally {
        this.checkingOut = false;
      }
    },
  },
};
</script>

<style>
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
