from seedrcc import Seedr
import json


def get_client():
    with open("seedr_token.json", "r") as f:
        data = json.load(f)

    device_code = data["device_code"]
    return Seedr.from_device_code(device_code)


def list_files():
    with get_client() as client:
        contents = client.list_contents()

        print("\nYour Seedr files:\n")

        for file in contents.files:
            print(
                f"[FILE] {file.name} | {file.size} bytes | "
                f"file_id: {file.file_id} | folder_file_id: {file.folder_file_id}"
            )

        print("\nYour Seedr folders:\n")

        for folder in contents.folders:
            print(
                f"[FOLDER] {folder.name} | ID: {folder.id}"
            )


if __name__ == "__main__":
    list_files()
