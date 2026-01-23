import axios from "axios";

// WARNING: In serverless, memory is not persistent.
// We only use this to temporarily show the device code.
// The token will be copied manually by the user.
globalThis.seedrDeviceCode = null;

export default async function handler(req, res) {
  try {
    const { data } = await axios.get("https://www.seedr.cc/rest/device/add");

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
    console.error(err.message);
    res.status(500).send("Failed to create device code");
  }
}
