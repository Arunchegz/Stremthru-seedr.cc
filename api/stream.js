import axios from "axios";

export default async function stream(req, res) {
  try {
    const token = process.env.SEEDR_TOKEN;

    if (!token) {
      return res.json({
        streams: [],
        error: "SEEDR_TOKEN not configured"
      });
    }

    const { data } = await axios.get(
      "https://www.seedr.cc/rest/folder",
      {
        headers: {
          "Authorization": `Bearer ${token}`,
          "User-Agent": "Mozilla/5.0",
          "Accept": "application/json"
        }
      }
    );

    const streams = [];

    for (const file of data.files || []) {
      if (file.stream_url) {
        streams.push({
          title: file.name,
          url: file.stream_url
        });
      }
    }

    res.json({ streams });
  } catch (err) {
    console.error(err.response?.data || err.message);
    res.status(500).json({ streams: [], error: "Seedr API error" });
  }
}
