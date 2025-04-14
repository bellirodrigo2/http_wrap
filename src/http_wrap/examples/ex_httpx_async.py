import asyncio

import httpx


async def main():
    proxy_url = "http://localhost:8080"
    transport = httpx.HTTPTransport(proxy=proxy_url)

    auth = httpx.BasicAuth("user", "pass")

    # Cria o request (sem auth aqui!)
    request = httpx.Request(
        method="POST",
        url="https://httpbin.org/post",
        headers={"User-Agent": "MyApp/1.0", "X-Custom-Header": "ChatGPT"},
        params={"search": "python"},
        data={"key1": "value1"},
        json={"extra": "data"},
        files={"file": ("filename.txt", b"conteudo do arquivo", "text/plain")},
        cookies={"sessionid": "123abc"},
    )

    # AUTH, timeout, verify, follow_redirects VAI PARA A SESSÃO

    async with httpx.AsyncClient(
        auth=auth,
        timeout=10.0,
        verify=True,
        follow_redirects=True,  # ,transport=transport
    ) as client:
        try:
            response = await client.send(request)

            print("Status:", response.status_code)
            print("Body:", response.json())

        except httpx.RequestError as e:
            print("Erro na requisição:", e)

    # Criando uma sessão reutilizável
    async with httpx.AsyncClient(
        # transport=transport,
        headers={
            "User-Agent": "MyApp/1.0",
            "Accept": "application/json",
            "X-Session-Header": "Persistente",
        },
        cookies={"sessionid": "abc123"},
        auth=auth,
        timeout=10.0,
        verify=True,
        follow_redirects=True,
    ) as client:

        url = "https://httpbin.org/post"
        method = "POST"

        # Dados da requisição
        params = {"search": "python"}
        data = {
            "campo1": "valor1"
        }  # será sobrescrito por `json`, se ambos forem usados
        json_data = {"info": "dados em json", "ativo": True}
        files = {"arquivo": ("exemplo.txt", b"Conteudo do arquivo", "text/plain")}
        headers = {"X-Custom-Header": "valor123"}  # sobrescreve header da sessão

        try:
            response = await client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files,
                headers=headers,
                cookies={"extra_cookie": "value"},  # adiciona aos da sessão
            )

            print("Status:", response.status_code)
            print("Headers:", response.headers)
            print("JSON:", response.json())

        except httpx.RequestError as e:
            print("Erro na requisição:", e)


asyncio.run(main())
