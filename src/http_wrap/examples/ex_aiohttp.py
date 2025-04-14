import asyncio

import aiohttp
from aiohttp import BasicAuth


async def main():
    proxy_url = "http://localhost:8080"
    auth = BasicAuth("user", "pass")

    # --- Primeira requisição (manual) ---
    async with aiohttp.ClientSession(auth=auth) as session:
        try:
            async with session.post(
                url="https://httpbin.org/post",
                proxy=proxy_url,
                headers={"User-Agent": "MyApp/1.0", "X-Custom-Header": "ChatGPT"},
                params={"search": "python"},
                # data={"key1": "value1"},  # Envia como x-www-form-urlencoded
                json={"extra": "data"},  # Ignorado se `data` estiver presente
                cookies={"sessionid": "123abc"},
                timeout=aiohttp.ClientTimeout(total=10),
                ssl=True,  # True = verify
            ) as response:

                print("Status:", response.status)
                print("Body:", await response.json())

        except aiohttp.ClientError as e:
            print("Erro na requisição:", e)

    # --- Segunda requisição (sessão persistente) ---
    headers = {
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
        "X-Session-Header": "Persistente",
    }

    cookies = {"sessionid": "abc123"}

    async with aiohttp.ClientSession(
        headers=headers,
        cookies=cookies,
        auth=auth,
        timeout=aiohttp.ClientTimeout(total=10),
    ) as session:

        url = "https://httpbin.org/post"
        method = "POST"

        params = {"search": "python"}
        data = {"campo1": "valor1"}
        json_data = {"info": "dados em json", "ativo": True}
        headers_override = {"X-Custom-Header": "valor123"}
        files = {"arquivo": aiohttp.FormData()}
        files["arquivo"].add_field(
            "arquivo",
            b"Conteudo do arquivo",
            filename="exemplo.txt",
            content_type="text/plain",
        )

        try:
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers_override,
                cookies={"extra_cookie": "value"},
            ) as response:

                print("Status:", response.status)
                print("Headers:", response.headers)
                print("JSON:", await response.json())
                print(response.url)
                print(response.host)
                print(response.url.port)
                print(response.url.scheme)

        except aiohttp.ClientError as e:
            print("Erro na requisição:", e)


asyncio.run(main())
# aiohttp.ClientResponse()
