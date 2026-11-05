<template>
  <div>
    <Navbar :user="name" :signed="signed" />
    <div class="container">
      <h1 class="cart-title">Your Shopping Cart</h1>
      <div class="row">
        <div class="col-md-8">
          <div v-for="cartItem in cartItems" :key="cartItem.productID" class="mb-3">
            <Cart_Item :cartItem="cartItem" :token="token" @updateCart="fetchCartItems" @deleteItem="fetchCartItems" />
          </div>
          <div v-if="cartItems.length === 0" class="card-body text-center">
            <h4>Your cart is empty.</h4>
            <router-link to="/" class="btn btn-primary">Continue Shopping</router-link>
          </div>
        </div>
        <div class="col-md-4 right-pane">
          <form @submit.prevent="applyCouponCode">
            <div class="input-group mb-3">
              <input type="text" class="form-control" placeholder="Coupon Code" v-model="couponCode" />
              <button class="btn btn-outline-secondary" type="submit">Apply</button>
            </div>
          </form>
          <button v-if="appliedCode" class="btn btn-link" type="button" @click="removeCoupon">
            Remove {{ appliedCode }}
          </button>
          <p v-if="message" class="coupon-message">{{ message }}</p>
          <div class="cart-total">Subtotal: ₹{{ subtotal }}</div>
          <div v-if="discountAmount" class="cart-total">Discount: −₹{{ discountAmount }}</div>
          <div class="cart-total">Total: ₹{{ total }}</div>
          <button type="button" class="btn btn-primary checkout-btn" @click="checkout" :disabled="!cartItems.length">
            Checkout
          </button>
        </div>
      </div>
      <RecommendationRow
        title="You might also like"
        :items="recommendations"
        :signed="signed"
        @added="fetchCartItems"
      />
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Cart_Item from "@/components/Cart_Item.vue";
import Navbar from "@/components/Navbar.vue";
import RecommendationRow from "@/components/RecommendationRow.vue";
import "../assets/style.css";

export default {
  components: { Navbar, Cart_Item, RecommendationRow },
  data() {
    return {
      cartItems: [],
      recommendations: [],
      couponCode: "",
      appliedCode: null,
      subtotal: 0,
      discountAmount: 0,
      total: 0,
      message: "",
      signed: sessionStorage.getItem("signed") === "true",
      name: sessionStorage.getItem("name") || "",
      token: sessionStorage.getItem("accessToken"),
    };
  },
  mounted() {
    this.fetchCartItems();
  },
  methods: {
    applyQuote(quote) {
      this.cartItems = quote.cart || [];
      this.subtotal = quote.subtotal || 0;
      this.discountAmount = quote.discount_amount || 0;
      this.total = quote.total || 0;
      this.appliedCode = quote.coupon_code;
      if (quote.message) this.message = quote.message;
    },
    fetchCartItems() {
      axios
        .get("/api/shopping_cart")
        .then((response) => this.applyQuote(response.data))
        .catch((error) => {
          if (error.response?.status === 401) this.$router.push("/login");
        });
      axios.get("/api/recommendations/cart").then((response) => {
        this.recommendations = response.data.recommendations || [];
      });
    },
    applyCouponCode() {
      axios
        .post("/api/shopping_cart/apply_coupon", { coupon_code: this.couponCode })
        .then((response) => this.applyQuote(response.data))
        .catch((error) => {
          this.message = error.response?.data?.error || "Could not apply that coupon.";
        });
    },
    removeCoupon() {
      axios.post("/api/shopping_cart/remove_coupon").then((response) => {
        this.message = "Coupon removed.";
        this.couponCode = "";
        this.applyQuote(response.data);
      });
    },
    checkout() {
      axios
        .post("/api/shopping_cart/checkout")
        .then((response) => {
          sessionStorage.setItem("cartItems", JSON.stringify(response.data.cart_items));
          sessionStorage.setItem("totalAmount", response.data.total);
          this.$router.push("/order-confirmation");
        })
        .catch((error) => {
          alert(error.response?.data?.error || "Checkout failed.");
        });
    },
  },
};
</script>

<style scoped>
.cart-total {
  font-size: 20px;
  margin-top: 8px;
  text-align: center;
}
.checkout-btn {
  font-size: 18px;
  display: block;
  margin: 16px auto;
}
.right-pane {
  position: sticky;
  top: 20px;
  background-color: white;
  padding: 16px;
  border: 1px solid #ccc;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.coupon-message {
  text-align: center;
  color: #1e7a46;
}
</style>
