import express from "express";
import authorize from "./api/authorize.js";
import callback from "./api/callback.js";
import stream from "./api/stream.js";
import manifest from "./api/manifest.js";

const app = express();
app.use(express.json());

app.get("/", (req, res) => {
  res.send("Seedr Stremio Addon is running");
});

app.get("/api/authorize", authorize);
app.get("/api/callback", callback);
app.get("/api/stream", stream);
app.get("/api/manifest.json", manifest);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log("Server running on port", PORT);
});
