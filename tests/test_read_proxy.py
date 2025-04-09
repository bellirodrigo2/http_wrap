from datetime import timedelta
from unittest.mock import Mock

import pytest
import requests

from http_wrap.proxy import make_proxy
from http_wrap.response import ResponseInterface


# Teste de leitura da propriedade 'status_code'
def test_status_code():
    # Criando uma resposta simulada de requests
    mock_response = Mock(spec=requests.Response)
    mock_response.status_code = 200
    mock_response.text = "OK"

    # Criando o Proxy
    proxy = make_proxy(mock_response, ResponseInterface, {}, {})

    # Testando o método `status_code`
    assert proxy.status_code == 200


# Teste de leitura da propriedade 'text'
def test_text():
    # Criando uma resposta simulada de requests
    mock_response = Mock(spec=requests.Response)
    mock_response.text = "Hello World"

    # Criando o Proxy
    proxy = make_proxy(mock_response, ResponseInterface, {}, {})

    # Testando o método `text`
    assert proxy.text == "Hello World"


# Teste de leitura da propriedade 'json'
def test_json():
    # Criando uma resposta simulada de requests
    mock_response = Mock(spec=requests.Response)
    mock_response.json.return_value = {"key": "value"}

    # Criando o Proxy
    proxy = make_proxy(mock_response, ResponseInterface, {}, {})

    # Testando o método `json`
    assert proxy.json() == {"key": "value"}


# Teste de leitura de 'elapsed'
def test_elapsed():
    # Criando uma resposta simulada de requests
    mock_response = Mock(spec=requests.Response)
    mock_response.elapsed = timedelta(seconds=2)

    # Criando o Proxy
    proxy = make_proxy(mock_response, ResponseInterface, {}, {})

    # Testando o método `elapsed`
    assert proxy.elapsed == timedelta(seconds=2)


# Teste de sobrescrita de método usando `overwrite`
def test_overwrite_method():
    # Criando uma resposta simulada de requests
    mock_response = Mock(spec=requests.Response)
    mock_response.status_code = 200

    # Sobrescrevendo o método `status_code`
    overwrite = {"status_code": lambda self: 404, "__str__": lambda self: "KKKKKKKK"}
    # Criando o Proxy com o método sobrescrito
    proxy = make_proxy(mock_response, ResponseInterface, {}, overwrite)

    # Testando o método sobrescrito `status_code`
    assert proxy.status_code == 404


# Teste de mapeamento de método usando `keys_map`
def test_keys_map_method():
    # Criando uma resposta simulada de requests
    mock_response = Mock(spec=requests.Response)
    mock_response.text = "Mapped Text"

    # Mapeando o nome do método
    keys_map = {"text": "text"}

    # Criando o Proxy com o mapeamento
    proxy = make_proxy(mock_response, ResponseInterface, keys_map, {})

    # Testando o método mapeado `text`
    assert proxy.text == "Mapped Text"


# Teste para a propriedade 'url'
def test_url():
    # Criando uma resposta simulada de requests
    mock_response = Mock(spec=requests.Response)
    mock_response.url = "http://example.com"

    # Criando o Proxy
    proxy = make_proxy(mock_response, ResponseInterface, {}, {})

    # Testando a propriedade `url`
    assert proxy.url == "http://example.com"
