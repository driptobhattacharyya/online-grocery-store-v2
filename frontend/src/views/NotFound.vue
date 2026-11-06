<template>
  <main class="container py-5 text-center">
    <p class="display-1 fw-bold text-success mb-2">404</p>
    <h1 class="h3 mb-3">Page not found</h1>
    <p class="text-muted mb-4">
      We couldn't find <code>{{ $route.fullPath }}</code>. It may have moved or
      never existed.
    </p>
    <router-link to="/" class="btn btn-success">Back to the store</router-link>
  </main>
</template>

<script>
export default {
  name: "NotFound",
};
</script>
