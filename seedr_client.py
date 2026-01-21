import requests

class SeedrClient:
    BASE = "https://www.seedr.cc/rest"

    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("Seedr access token is required")
        self.token = access_token

    def _get(self, endpoint, params=None):
        if params is None:
            params = {}
        params["access_token"] = self.token

        r = requests.get(self.BASE + endpoint, params=params)
        if r.status_code != 200:
            raise Exception(f"Seedr API error: {r.status_code} - {r.text}")
        return r.json()

    def _post(self, endpoint, data=None):
        if data is None:
            data = {}
        data["access_token"] = self.token

        r = requests.post(self.BASE + endpoint, data=data)
        if r.status_code != 200:
            raise Exception(f"Seedr API error: {r.status_code} - {r.text}")
        return r.json()

    # Account info (to test token validity)
    def account(self):
        return self._get("/account")

    # Root folder listing
    def list_root(self):
        return self._get("/folder")

    # List a specific folder
    def list_folder(self, folder_id):
        return self._get("/folder", {"folder_id": folder_id})

    # Get file streaming URL
    def get_stream_url(self, file_id):
        data = self._get("/file", {"file_id": file_id})
        if "url" not in data:
            raise Exception("No stream URL returned by Seedr")
        return data["url"]

    # Optional: delete file
    def delete_file(self, file_id):
        return self._post("/file/delete", {"file_id": file_id})

    # Optional: delete folder
    def delete_folder(self, folder_id):
        return self._post("/folder/delete", {"folder_id": folder_id})