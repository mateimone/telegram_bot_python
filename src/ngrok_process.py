import requests

class Ngrok:

    @staticmethod
    async def get_ngrok_url(port: str):
        try:
            req = requests.get(f"http://127.0.0.1:{port}/api/tunnels")
            tunnels = req.json().get('tunnels', [])
            public_url = tunnels[0]['public_url'] if tunnels else None
            print(f"Ngrok url: {public_url}")
            return public_url
        except Exception as e:
            print(f"Error: {e}")
            return None
