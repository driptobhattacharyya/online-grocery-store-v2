<template>
  <div>
    <Navbar :user="name" :signed="signed" @ChildEvent="handleChildEvent" />
    <div class="container">
      <h1 class="cart-title">Your Shopping Cart</h1>
      <div class="row">
        <div class="col-9">
          <div class="row">
            <div class="add-gap"></div>
            <div
              class="col-12"
              v-for="cartItem in cartItems"
              :key="cartItem.id"
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
          <!-- <form method="POST">
            <div class="input-group mb-3">
              <input
                type="text"
                class="form-control"
                placeholder="Coupon Code"
                aria-label="Coupon Code"
                aria-describedby="apply-coupon-button"
                v-model="couponCode"
                name="coupon_code"
              />
              <button
                class="btn btn-outline-secondary"
                type="submit"
                id="apply-coupon-button"
                @click.prevent="applyCouponCode"
              >
                Apply
              </button>
            </div>
          </form> -->
          <div class="cart-total">Total: ₹{{ calculateTotalAmount() }}</div>
          <div>
            <input type="hidden" name="totalPrice" :value="totalAmount" />
            <button
              type="submit"
              class="btn btn-primary checkout-btn"
              name="checkout"
              value="true"
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
        <a href="/" class="btn btn-primary">Continue Shopping</a>
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
import router from "@/router";
import "../assets/style.css";

export default {
  components: {
    Navbar,
    Cart_Item,
  },
  data() {
    return {
      cartItems: [],
      couponCode: "",
      totalAmount: 0,
      signed: false,
      user: "",
      token: sessionStorage.getItem("accessToken"),
    };
  },
  mounted() {
    this.fetchCartItems();
    this.signed = sessionStorage.getItem("signed");
    this.name = sessionStorage.getItem("name");
    // console.log(sessionStorage.getItem("accessToken"))
  },
  methods: {
    fetchCartItems() {
      try {
        console.log(this.token);
        axios
          .get("http://localhost:5000/api/shopping_cart", {
            mode: "no-cors",
            headers: {
              Authorization: "Bearer " + this.token,
            },
          })
          .then((response) => {
            this.received_data = response.data;
            console.log(this.received_data);
            this.cartItems = this.received_data.cart;
            console.log(this.cartItems);
          });
        // this.calculateTotalAmount();
      } catch (error) {
        console.error("Error:", error);
      }
    },
    calculateTotalAmount() {
      this.totalAmount = this.cartItems.reduce(
        (total, item) => total + item.price * item.quantity,
        0
      );
      return this.totalAmount;
    },
    checkout() {
      try {
        axios.post(
          "http://127.0.0.1:5000/api/shopping_cart/checkout",
          {
            "totalPrice": this.totalAmount,
          },
          {
            mode: "no-cors",
            headers: {
              Authorization: "Bearer " + this.token,
            },
          }
        );
        sessionStorage.setItem('cartItems', JSON.stringify(this.cartItems));
        sessionStorage.setItem('totalAmount', this.totalAmount);
        this.$router.push("/order-confirmation")
      } catch (error) {
        console.error("Error:", error);
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
