
# CHATBOTS - ZETA

ZETA é um aplicativo desenvolvido para auxiliar produtores rurais na criação de animais, oferecendo treinamentos e conteúdos técnicos e práticos que promovem o aprimoramento de seus conhecimentos.

Este repositório há os dois chatbots utilizados no aplicativo:

- Sindi:utilizado para tirar dúvidas sobre o conteúdo do curso, como aulas, lei e normas técnicas abordadas em cada aula, além do próprio conteúdo da aula;
- Canchim:utilizado para retornar os cursos que estão disponíveis a partir do assunto que o usuário forneceu como parâmetro.

## Linguagens utilizadas
Para o desenvolvimento dos agentes foi utilizada a linguagem Python.

## Frameworks
Foi utilizado os seguintes frameworks:
* Flask
* Langchain

## Modelos de LLM
Para o desenvolvimento do agentes principais utilizamos o modelo *Gemini 2.5 Flash*, enquanto para o guardrail foi aplicado o modelo *Gemini 2.0 Flash-Lite* e para o juiz foi usado o modelo *GPT-4o Mini*.

## Configuração Inicial
1. Clone o repositório:
```bash
git clone https://github.com/ZETA-Inter/IA-chatbot-pesquisa.git
```
2. Abra o projeto na IDE de sua preferência;
3. Abra o terminal e instale as dependências do projeto:
```bash
pip install -r requirements.txt
```
4. Encontre o arquivo *local_test.py* e adicione o input do usuário - escolha uma das opções do dicionário ou escreva a sua própria pergunta;
5. espere alguns instantes e receberá o retorno do chatbot escolhido.

## Desenvolvedores
Desenvolvido com dedicação pela equipe de tecnologia ZETA:
- [Raquel Tolomei](https://github.com/RaquelTolomei)  
- [Sofia Rodrigues Santana](https://github.com/SofiaRSantana)  
- [Sophia Laurindo Gasparetto](https://github.com/sosogasp)  

## Contato
Para mais informações ou suporte, entre em contato através de nosso site ou envie um email para appzetaofc@gmail.com.

## Licença  
[MIT](https://choosealicense.com/licenses/mit/)

## Copyright
© **Copyright ZETA 2025**  

Todos os direitos reservados.
Este software é protegido por leis de direitos autorais. Não é permitida a cópia, distribuição ou modificação sem permissão do autor.






