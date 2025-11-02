import requests


response = requests.post(url='http://18.207.93.176:8000/search_agent', json={"prompt" : "O que é a lei 8.171/1991?"})

print(response.text)