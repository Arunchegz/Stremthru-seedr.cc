export default function handler(req, res) {
  res.json({
    id: "org.seedr.stremio",
    version: "1.0.0",
    name: "Seedr Streams",
    description: "Stream your Seedr files in Stremio using official device authentication",
    resources: ["stream"],
    types: ["movie", "series", "other"],
    catalogs: []
  });
}
