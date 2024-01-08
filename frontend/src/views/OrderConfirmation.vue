<template>
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-md-6 order-card">
        <h2 class="order-title">Order Confirmation</h2>
        <ul class="item-list">
          <li class="item" v-for="item in cartItems" :key="item.id">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-quantity">Quantity: {{ item.quantity }}</span>
          </li>
        </ul>
        <p class="total-price">Total Price: ₹{{ totalAmount }}</p>
        <a href="/" class="btn btn-primary back-btn"
          >Back to Home</a
        >
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      cartItems: [], // Pass the cart items as a prop from the previous component or fetch them from the store
      totalAmount: 0, // Pass the total amount as a prop from the previous component or fetch it from the store
    };
  },
  created() {
    // Retrieve data from sessionStorage
    const storedCartItems = sessionStorage.getItem('cartItems');
    this.cartItems = storedCartItems ? JSON.parse(storedCartItems) : [];

    const storedTotalAmount = sessionStorage.getItem('totalAmount');
    this.totalAmount = storedTotalAmount ? parseFloat(storedTotalAmount) : 0;
  },
  mounted(){
    console.log(this.cartItems)
    console.log(this.totalAmount)
  }
};
</script>

<style scoped>
/* Add your custom styles here */
.order-card {
  background-color: #fff;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 30px;
  margin-top: 50px;
}

.order-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.305);
}

.order-title {
  font-size: 24px;
  margin-bottom: 15px;
}

.item-list {
  list-style: none;
  padding: 0;
}

.item {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 5px;
  background-color: #f8f9fa;
}

.item-name {
  font-size: 18px;
  margin-bottom: 5px;
}

.item-quantity {
  font-size: 16px;
  color: #6c757d;
}

.total-price {
  font-size: 24px;
  margin-top: 20px;
}

.back-btn {
  margin-top: 20px;
}
</style>
