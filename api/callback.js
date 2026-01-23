import axios from "axios";

export default async function callback(req, res) {
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
          "User-Agent": "Mozilla/5.0",
          "Accept": "application/json",
          "Content-Type": "application/json"
        }
      }
    );

    if (!data.access_token) {
      return res.send("Device not approved yet. Approve and try again.");
    }

    res.send(`
      <h2>Authorization Successful</h2>
      <p>Your Seedr Access Token:</p>
      <pre>${data.access_token}</pre>
      <p>Now save this token as <b>SEEDR_TOKEN</b> in Railway Variables.</p>
      <p>Then restart your service.</p>
    `);
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).send("Authorization failed");
  }
}
