import axios from "axios";

globalThis.seedrDeviceCode = null;

export default async function handler(req, res) {
  try {
    const { data } = await axios.get(
      "https://www.seedr.cc/rest/device/add",
      {
        headers: {
          "User-Agent": "Seedr-Stremio-Addon",
          "Accept": "application/json"
        }
      }
    );

    globalThis.seedrDeviceCode = data.device_code;

    res.setHeader("Content-Type", "text/html");
    res.end(`
      <h2>Seedr Authorization</h2>
      <ol>
        <li>Open <a href="https://www.seedr.cc/devices" target="_blank">
          https://www.seedr.cc/devices</a></li>
        <li>Enter this code:</li>
      </ol>
      <h1>${data.user_code}</h1>
      <p>After approving, open:</p>
      <a href="/api/callback">/api/callback</a>
    `);
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).send("Failed to create device code");
  }
}
