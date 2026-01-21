import requests

class SeedrClient:
    BASE = "https://www.seedr.cc/rest"

    def __init__(self, token):
        if not token:
            raise ValueError("SEEDR_TOKEN is not set")
        self.token = token

    def _get(self, path):
        url = f"{self.BASE}{path}"
        r = requests.get(url, params={"access_token": self.token})
        print("Seedr request:", r.url)
        print("Seedr status:", r.status_code)
        print("Seedr body:", r.text)
        r.raise_for_status()
        return r.json()

    def list_root(self):
        return self._get("/folder")

    def list_folder(self, folder_id):
        return self._get(f"/folder/{folder_id}")

    def get_stream_url(self, file_id):
        return f"https://www.seedr.cc/rest/file/{file_id}?access_token={self.token}"