import asyncio
import getgrass_proxy
import os
from dotenv import load_dotenv

load_dotenv()

grass_userid = os.getenv("GRASS_USERID")

async def test_connect_to_wss(http_proxy, user_id):
    try:
        await getgrass_proxy.connect_to_wss(http_proxy, user_id)
        return True
    except Exception as e:
        print(f"Error occurred while testing proxy {http_proxy}: {e}")
        return False

async def test_proxies():
    good_proxies = []
    with open('proxy-list.txt', 'r') as file:
        proxies = file.readlines()
        proxies = [proxy.strip() for proxy in proxies if proxy.strip()]

    for proxy in proxies:
        if await test_connect_to_wss(proxy, user_id):
            good_proxies.append(proxy)
    
    with open('good_proxy-list.txt', 'w') as good_proxy_file:
        for proxy in good_proxies:
            good_proxy_file.write(proxy + '\n')

if __name__ == '__main__':
    user_id = "2h3JHQeoIEy1pwfdw3gzEDu0AE8"  # Replace with your user ID
    
    # Run the coroutine in an event loop
    asyncio.run(test_proxies())
