module.exports = {
  devServer: {
    port: 8080,
    proxy: {
      "/api": {
        target: process.env.VUE_APP_PROXY_TARGET || "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
};
