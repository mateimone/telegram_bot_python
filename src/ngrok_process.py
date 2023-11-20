import requests

class Ngrok:

    @staticmethod
    async def get_ngrok_url(port: str):
        try:
            req = requests.get(f"http://127.0.0.1:{port}/api/tunnels")
            tunnels = req.json().get('tunnels', [])
            public_url = tunnels[0]['public_url'] if tunnels else None
            print(public_url)
            return public_url
        except Exception as e:
            print(f"Error: {e}")
            return None

    # @staticmethod
    # async def start_ngrok():
    #     match = None
    #     try:
    #         cmd = ["ngrok", "http", "http://127.0.0.1:4040"]
    #         ngrok = await asyncio.create_subprocess_exec(
    #             *cmd,
    #             stdout=asyncio.subprocess.PIPE,
    #             stderr=asyncio.subprocess.PIPE
    #         )
    #         global pid
    #         pid = ngrok.pid
    #
    #         while True:
    #             line = await ngrok.stdout.readline()
    #             if not line:
    #                 break
    #             line = line.decode().strip()
    #             print(line)  # Optionally print the output for debugging
    #
    #             # Use regex to find the URL
    #             match = re.search(r'http://[a-z0-9]+.ngrok-free.app', line)
    #             if match:
    #                 print(f"Ngrok URL: {match.group(0)}")
    #                 break
    #     except Exception as e:
    #         print(e)
    #
    #     # print(Ngrok.get_ngrok_url())
    #     # return Ngrok.get_ngrok_url()
    #
    #     return match.group(0)