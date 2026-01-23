import axios from "axios";

globalThis.seedrDeviceCode = null;

export default async function handler(req, res) {
  try {
    const { data } = await axios.post(
      "https://www.seedr.cc/rest/device/add",
      {}, // empty body
      {
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
          "Accept": "application/json",
          "Content-Type": "application/json",
          "Origin": "https://www.seedr.cc",
          "Referer": "https://www.seedr.cc/devices"
        }
      }
    );

    globalThis.seedrDeviceCode = data.device_code;

    res.setHeader("Content-Type", "text/html");
    res.end(`
      <h2>Seedr Authorization</h2>
      <p>1. Open: <a href="https://www.seedr.cc/devices" target="_blank">
      https://www.seedr.cc/devices</a></p>
      <p>2. Enter this code:</p>
      <h1>${data.user_code}</h1>
      <p>3. After approval, open:</p>
      <a href="/api/callback">/api/callback</a>
    `);

  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).send("Failed to create device code");
  }
}
