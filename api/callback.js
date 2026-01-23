import axios from "axios";

export default async function handler(req, res) {
  try {
    const deviceCode = globalThis.seedrDeviceCode;

    if (!deviceCode) {
      return res.send("No device code found. Run /api/authorize first.");
    }

    const { data } = await axios.post(
      "https://www.seedr.cc/rest/device/code",
      { device_code: deviceCode },
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

    if (!data.access_token) {
      return res.send("Device not approved yet. Please approve and try again.");
    }

    res.setHeader("Content-Type", "text/html");
    res.end(`
      <h2>Authorization successful!</h2>
      <p>Your access token:</p>
      <pre>${data.access_token}</pre>
      <p>Save this as <b>SEEDR_TOKEN</b> in Vercel Environment Variables</p>
    `);

  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).send("Authorization failed");
  }
}
