import asyncio
import subprocess
import time
import requests
import os
import signal
import re
from threading import Thread, Lock

pid = -1

class Ngrok:
    _event_loop = None
    _lock = Lock()
    _is_closed = False

    # def __init__(self):
    #     super().__init__()

    # def run(self):
    #     try:
    #         # loop = asyncio.new_event_loop()
    #         # asyncio.set_event_loop(loop)
    #         # Ngrok._event_loop = loop
    #         # loop.run_until_complete(Ngrok.start_ngrok())
    #     except Exception as e:
    #         print(f"Exception in Ngrok: {e}")

    @staticmethod
    def get_event_loop():
        return Ngrok._event_loop

    @staticmethod
    async def get_ngrok_url(port: str):
        try:
            # r0 = requests.get("http://127.0.0.1:4040/api/tunnels")
            # r1 = requests.get("http://127.0.0.1:4041/api/tunnels")
            # r2 = requests.get("http://127.0.0.1:4042/api/tunnels")
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

    # @staticmethod
    # def stop_ngrok():
    #     try:
    #         global pid
    #         os.kill(pid, signal.SIGTERM)
    #         pid = -1
    #     except OSError as e:
    #         print(f"Error terminating process: {e}")

    # @staticmethod
    # async def terminate_ngrok():
    #     try:
    #         process = await asyncio.create_subprocess_exec(
    #             "tskill", "/A", "ngrok",
    #             stdout=asyncio.subprocess.PIPE,
    #             stderr=asyncio.subprocess.PIPE
    #         )
    #
    #         stdout, stderr = await process.communicate()
    #
    #         if process.returncode == 0:
    #             Ngrok._is_closed = True
    #             print("ngrok terminated successfully.")
    #             print(stdout.decode())
    #         else:
    #             print(f"Error terminating ngrok: {stderr.decode()}")
    #
    #     except OSError as e:
    #         print(f"Execution failed: {e}")


if __name__ == "__main__":
    pass
    # n = Ngrok()
    # n.start_ngrok()
    # n.terminate_ngrok()

