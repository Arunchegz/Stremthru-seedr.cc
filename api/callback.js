import axios from "axios";

export default async function handler(req, res) {
  try {
    const deviceCode = globalThis.seedrDeviceCode;

    if (!deviceCode) {
      return res.send("No device code found. Run /api/authorize first.");
    }

    const { data } = await axios.get(
      `https://www.seedr.cc/rest/device/code?device_code=${deviceCode}`,
      {
        headers: {
          "User-Agent": "Seedr-Stremio-Addon",
          "Accept": "application/json"
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
      <p>Save this in Vercel as <b>SEEDR_TOKEN</b></p>
    `);
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).send("Authorization failed");
  }
}
