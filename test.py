import requests


response = requests.post(url='https://ia-chatbot-pesquisa-j2ka.onrender.com/programs_agent', json={"prompt" : "qual e a lei 77/2018?"})

print(response.text)