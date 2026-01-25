from seedrcc import Seedr, Token
import os

TOKEN_FILE = "seedr_token.json"

def save_token(token: Token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token.to_json())

def get_client() -> Seedr:
    if not os.path.exists(TOKEN_FILE):
        raise RuntimeError("seedr_token.json not found. Token is missing.")

    with open(TOKEN_FILE, "r") as f:
        token = Token.from_json(f.read())

    return Seedr(token, on_token_refresh=save_token)
