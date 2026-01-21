import requests

class SeedrClient:
    def __init__(self, token):
        self.token = token
        self.base = "https://www.seedr.cc/rest"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Seedr-Stremio-Addon"
        }

    def list_root(self):
        r = requests.get(f"{self.base}/folder", headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_folder(self, folder_id):
        r = requests.get(f"{self.base}/folder/{folder_id}", headers=self.headers)
        r.raise_for_status()
        return r.json()

    def get_stream_url(self, file_id):
        # Token based streaming, same method MediaFusion uses
        return f"https://www.seedr.cc/rest/file/{file_id}?token={self.token}"