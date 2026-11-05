import axios from "axios";

export async function downloadSalesReport() {
  const start = await axios.post("/api/manager/prepare_report");
  const taskId = start.data.task_id;
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const status = await axios.get(`/api/manager/report/${taskId}`);
    if (status.data.state === "SUCCESS") {
      const file = await axios.get(`/api/manager/report/${taskId}/download`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(file.data);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "sales_report.csv");
      document.body.appendChild(link);
      link.click();
      link.remove();
      return;
    }
    if (status.data.state === "FAILURE") {
      throw new Error("The sales report failed.");
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
  }
  throw new Error("The sales report took too long.");
}
