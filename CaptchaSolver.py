import asyncio
import random

from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector

class CaptchaSolver:
    def __init__(self, cap_client_api_key, proxy=None, is_used_proxy = False):
        self.cap_client_api_key = cap_client_api_key
        self.proxy = proxy
        self.is_used_proxy = is_used_proxy

        self.session = ClientSession(
            connector=ProxyConnector.from_url(f"http://{proxy}") if is_used_proxy else TCPConnector()
        )

        self.session.headers.update({
            'User-Agent': self.get_user_agent()
        })

    @staticmethod
    def get_user_agent():
        random_version = f"{random.uniform(520, 540):.2f}"
        return (f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random_version} (KHTML, like Gecko)'
                f' Chrome/126.0.0.0 Safari/{random_version} Edge/126.0.0.0')

    async def make_request(self, method: str = 'GET', url: str = None, headers=None, json: dict = None):
        async with self.session.request(method=method, url=url, headers=headers, json=json) as response:
            if response.status in [200, 201]:
                return await response.json(content_type=None)
            raise RuntimeError(f"Bad request to Solver API. Response status: {response.status}")

    async def create_task_for_captcha(self):
        url = 'https://api.capmonster.cloud/createTask'

        payload = {
            "clientKey": self.cap_client_api_key,
            "task": {
                "type": "TurnstileTask" if self.is_used_proxy else 'TurnstileTaskProxyless',
                "websiteURL": "https://faucet.movementnetwork.xyz/",
                "websiteKey": "0x4AAAAAAAya3vu3EyR3DGUk",
                "userAgent": self.session.headers['User-Agent'],
            }
        }

        if self.is_used_proxy:
            proxy_tuple = self.proxy.split('@')

            proxy_login, proxy_password = proxy_tuple[0].split(':')
            proxy_address, proxy_port = proxy_tuple[1].split(':')

            payload['task'].update({
                "proxyType": "http",
                "proxyAddress": proxy_address,
                "proxyPort": proxy_port,
                "proxyLogin": proxy_login,
                "proxyPassword": proxy_password
            })

        response = await self.make_request(method="POST", url=url, json=payload)

        if response['errorId'] == 0:
            return response['taskId']
        raise RuntimeError('Bad request to CapMonster(Create Task)')

    async def get_captcha_key(self, task_id):
        url = 'https://api.capmonster.cloud/getTaskResult'

        payload = {
            "clientKey": self.cap_client_api_key,
            "taskId": task_id
        }

        total_time = 0
        timeout = 360
        while True:
            response = await self.make_request(method="POST", url=url, json=payload)

            if response['status'] == 'ready':
                return response['solution']['token']

            total_time += 5
            await asyncio.sleep(5)

            if total_time > timeout:
                raise RuntimeError('Can`t get captcha solve in 360 second')

    async def make_request_to_claim(self, token_resolved_captcha, claim_address):
        json_payload: dict = {
          "token": token_resolved_captcha,
          "address": claim_address,
          "network": "mevm",
          "config": {
            "holesky": {
              "network": "testnet",
              "url": "https://holesky.gateway.tenderly.co",
              "language": "evm"
            },
            "bardock": {
              "network": "testnet",
              "url": "https://testnet.bardock.movementnetwork.xyz/v1",
              "faucetUrl": "https://fund.testnet.bardock.movementnetwork.xyz",
              "language": "aptos"
            },
            "porto": {
              "network": "testnet",
              "url": "https://testnet.porto.movementnetwork.xyz/v1",
              "faucetUrl": "https://fund.testnet.porto.movementnetwork.xyz",
              "language": "aptos"
            },
            "mevm": {
              "network": "devnet",
              "url": "https://mevm.devnet.imola.movementlabs.xyz",
              "language": "evm"
            }
          }
        }

        async with self.session.request(method='POST', url='https://faucet.movementnetwork.xyz/api/rate-limit', headers=None, json=json_payload) as response:
            if response.status in [200, 201]:
                return await response.json(content_type=None)
            raise RuntimeError(f"Bad request to claim token in faucet. Response status: {response.status}")
