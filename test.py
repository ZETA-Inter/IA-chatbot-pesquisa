import requests


response = requests.post(url='http://50.19.29.44:8000/programs_agent', json={"prompt" : "O que é a lei 8.171/1991?"})

print(response.text)