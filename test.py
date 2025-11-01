import requests


response = requests.post(url='http://172.31.28.40:8000/programs_agent', json={"prompt" : "O que é a lei 8.171/1991?"})

print(response.text)