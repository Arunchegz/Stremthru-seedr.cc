import requests

class SeedrClient:
    BASE_URL = "https://www.seedr.cc/rest"

    def __init__(self, token):
        if not token:
            raise ValueError("SEEDR_TOKEN environment variable not set")
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {self.token}"
        }

    def _get(self, path, params=None):
        url = f"{self.BASE_URL}{path}"
        r = requests.get(url, headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def list_root(self):
        # Lists files & folders in root
        return self._get("/folder")

    def get_stream_url(self, file_id):
        data = self._get("/file", params={"file_id": file_id})
        return data["url"]