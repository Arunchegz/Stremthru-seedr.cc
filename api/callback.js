import axios from "axios";

export default async function handler(req, res) {
  try {
    const deviceCode = globalThis.seedrDeviceCode;

    if (!deviceCode) {
      return res.send("No device code found. Run /api/authorize first.");
    }

    const { data } = await axios.get(
      `https://www.seedr.cc/rest/device/code?device_code=${deviceCode}`
    );

    if (!data.access_token) {
      return res.send("Device not approved yet. Please approve and try again.");
    }

    res.setHeader("Content-Type", "text/html");
    res.end(`
      <h2>Authorization successful!</h2>
      <p>Your access token:</p>
      <pre>${data.access_token}</pre>
      <p>Now save it in Vercel:</p>
      <pre>vercel env add SEEDR_TOKEN</pre>
      <p>Paste this token when asked, then redeploy:</p>
      <pre>vercel --prod</pre>
    `);
  } catch (err) {
    console.error(err.message);
    res.status(500).send("Authorization failed");
  }
}
