import requests
from requests.auth import HTTPBasicAuth

# EXEMPLO COM PREPARE + SEND
req = requests.Request(
    method="POST",
    url="https://httpbin.org/post",
    headers={
        "User-Agent": "MyApp/1.0",
        "X-Custom-Header": "ChatGPT"
    },
    params={"search": "python"},  # irá aparecer na URL
    data={"key1": "value1"},       # form-urlencoded (padrão se json não usado)
    json={"extra": "data"},        # também envia JSON no corpo
    files={"file": ("filename.txt", b"conteúdo do arquivo", "text/plain")},
    cookies={"sessionid": "123abc"},
    auth=HTTPBasicAuth("user", "pass")
)

prepared: requests.PreparedRequest = req.prepare()

with requests.Session() as session:
    try:
        response = session.send(
            prepared,
            timeout=(5, 10),  # (connect_timeout, read_timeout)
            verify=True,      # ou path para certificado
            stream=False,     # se quiser consumir em partes
            allow_redirects=True,  # seguir redirects
            proxies={
                "http": "http://localhost:8080",
                "https": "http://localhost:8080"
            }
        )
        print("Status:", response.status_code)
        print("Body:", response.json())

    except requests.exceptions.RequestException as e:
        print("Erro na requisição:", e)

# EXEMPLO COM request

# Criando uma sessão reutilizável
session = requests.Session()

# Cabeçalhos padrão para a sessão
session.headers.update({
    "User-Agent": "MyApp/1.0",
    "Accept": "application/json",
    "X-Session-Header": "Persistente"
})

# Cookies persistentes na sessão
session.cookies.set("sessionid", "abc123")

# Dados da requisição
url = "https://httpbin.org/post"
method = "POST"
params = {
    "search": "python"
}
data = {
    "campo1": "valor1",
    "campo2": "valor2"
}
json_data = {
    "info": "dados em json",
    "ativo": True
}
files = {
    "arquivo": ("exemplo.txt", b"Conteúdo do arquivo", "text/plain")
}
headers = {
    "X-Custom-Header": "valor123"
}
proxies = {
    "http": "http://localhost:8080",
    "https": "http://localhost:8080"
}
try:
    response = session.request(
        method=method,
        url=url,
        params=params,
        data=data,
        json=json_data,   # ⚠️ Usar json sobrescreve `data` no corpo
        files=files,
        headers=headers,  # sobrescreve headers da sessão
        cookies={"extra_cookie": "value"},
        auth=HTTPBasicAuth("user", "pass"),
        timeout=(5, 15),  # (connect timeout, read timeout)
        allow_redirects=True,
        verify=True,      # pode ser False ou path para certificado
        stream=False,
        proxies=proxies
    )

    # Exibindo resposta
    print("Status:", response.status_code)
    print("Headers:", response.headers)
    print("JSON:", response.json())

except requests.exceptions.RequestException as e:
    print("Erro na requisição:", e)

requests.Response()