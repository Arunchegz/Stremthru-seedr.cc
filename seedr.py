import requests

class SeedrClient:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Seedr-Stremio-Addon"
        }
        self.base = "https://www.seedr.cc/rest"

    def list_root(self):
        return requests.get(f"{self.base}/folder", headers=self.headers).json()

    def get_folder(self, folder_id):
        return requests.get(f"{self.base}/folder/{folder_id}", headers=self.headers).json()

    def get_stream_url(self, file_id):
        # Token-based streaming
        return f"https://www.seedr.cc/rest/file/{file_id}?token={self.token}"