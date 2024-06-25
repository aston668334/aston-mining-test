import argparse
import asyncio
import random
import signal
import ssl
import json
import time
import uuid
from loguru import logger
import websockets
from websockets_proxy import Proxy, proxy_connect
import os
from dotenv import load_dotenv

load_dotenv()

grass_userid = os.getenv("GRASS_USERID")


# Async function to connect to WebSocket server
async def connect_to_wss(http_proxy, user_id, semaphore):
    async with semaphore:
        device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, http_proxy))
        logger.info(device_id)

        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(http_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                    extra_headers=custom_headers) as websocket:
                async def send_ping():
                    send_message = json.dumps(
                        {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                    logger.debug(send_message)
                    await websocket.send(send_message)
                    await asyncio.sleep(20)

                await asyncio.sleep(1)
                # asyncio.create_task(send_ping())
                response = await websocket.recv()
                message = json.loads(response)
                logger.info(message)
                if (message.get("action") == "AUTH") or (message.get("action") == "PONG") or (message.get("action") == "PING"):  # Checking if the action is "AUTH"
                    await websocket.close()
                    return http_proxy  # Return proxy if it's considered a good proxy based on "AUTH" action
        except asyncio.CancelledError:
            logger.info(f"Task for proxy {http_proxy} cancelled")
        except Exception as e:
            logger.error(e)
            logger.error(http_proxy)
            return None
        return None  # Return None if not a good proxy

async def connect_socket_proxy(http_proxy,semaphore):
    async with semaphore:
        WEBSOCKET_URL = "wss://nw.nodepay.ai:4576/websocket"
        SERVER_HOSTNAME = "nw.nodepay.ai"
        browser_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, http_proxy))
        logger.info(f"Browser ID: {browser_id}")

        try:
            proxy = Proxy.from_url(http_proxy)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            async with proxy_connect(WEBSOCKET_URL, proxy=proxy, ssl=ssl_context, server_hostname=SERVER_HOSTNAME,
                                        extra_headers=custom_headers) as websocket:
                logger.info("Connected to WebSocket")
                async for message in websocket:
                    data = json.loads(message)
                    if (data["action"] == "AUTH") or (data["action"] == "PONG") or (data["action"] == "PING") :
                        await websocket.close()
                        return http_proxy


        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Connection closed with error: {e.code} - {e.reason}")
            return None
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Connection closed normally")
            return None
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return None
        return None  # Return None if not a good proxy
        


async def test_proxies():
    semaphore = asyncio.Semaphore(300)  # Limiting to 100 simultaneous tests
    good_proxies = []
    
    with open('proxy-list.txt', 'r') as file:
        proxies = file.readlines()
        proxies = [proxy.strip() for proxy in proxies if proxy.strip()]

    # tasks = []
    # for proxy in proxies:
    #     tasks.append(connect_to_wss(proxy, grass_userid,semaphore))
    
    # results = await asyncio.gather(*tasks)
    # good_proxies = [proxy for proxy in results if proxy]
    
    # with open('good-grass-proxy-list.txt', 'w') as good_proxy_file:
    #     for proxy in good_proxies:
    #         good_proxy_file.write(proxy + '\n')


    tasks = []
    for proxy in proxies:
        tasks.append(connect_socket_proxy(proxy,semaphore))
    
    results = await asyncio.gather(*tasks)
    good_proxies = [proxy for proxy in results if proxy]
    
    with open('good-nodepay-proxy-list.txt', 'w') as good_proxy_file:
        for proxy in good_proxies:
            good_proxy_file.write(proxy + '\n')

if __name__ == '__main__':
    # Run the coroutine in an event loop
    n =100000
    # Filter and format the proxies
    filtered_proxies = []

    with open('../PROXY-List/http.txt', 'r') as file:
        lines = file.readlines()

    for line in lines[:n]:
        ip, port = line.strip().split(':')
        filtered_proxies.append(f'http://{ip}:{port}')

    with open('../PROXY-List/socks4.txt', 'r') as file:
        lines = file.readlines()

    for line in lines[:n]:
        ip, port = line.strip().split(':')
        filtered_proxies.append(f'socks4://{ip}:{port}')


    # Read the contents of http.txt
    with open('../PROXY-List/socks5.txt', 'r') as file:
        lines = file.readlines()

    for line in lines[:n]:
        ip, port = line.strip().split(':')
        filtered_proxies.append(f'socks5://{ip}:{port}')

    # Read the contents of http.txt
    with open('./good-grass-proxy-list-filterd.txt', 'r') as file:
        lines = file.readlines()
    for line in lines:
        filtered_proxies.append(line.strip())

    # Read the contents of http.txt
    with open('./good-nodepay-proxy-list.txt', 'r') as file:
        lines = file.readlines()
    for line in lines:
        filtered_proxies.append(line.strip())

    filtered_proxies = list(dict.fromkeys(filtered_proxies))
    # Write the filtered proxies to proxy-list.txt
    with open('proxy-list.txt', 'w') as file:
        for proxy in filtered_proxies:
            file.write(proxy + '\n')

    print("Filtered proxies have been written to proxy-list.txt")
    asyncio.run(test_proxies())
