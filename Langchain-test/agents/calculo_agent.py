from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
from langchain.callbacks import StdOutCallbackHandler
from openai import OpenAI
from dotenv import load_dotenv
from flask import session
import os, re

load_dotenv()

client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY'))

def calculo(input_chat):
    laudo_content = session.get("laudo_content", "Sem laudo na sessão")
    print("laudo fornecido - agente calculo:", laudo_content)
    print("chat agente calculo:", input_chat)

    try:
        # Lista para armazenar volumes
        volumes = []

        # Identificar dimensões diretamente no laudo_content usando regex
        dimensoes_regex = re.findall(r"(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)", laudo_content)
        for dimensoes_str in dimensoes_regex:
            # Converter as dimensões para float
            dimensoes = list(map(float, dimensoes_str))
            # Calcular o volume
            volume = dimensoes[0] * dimensoes[1] * dimensoes[2] * 0.52
            # Armazenar o volume na lista
            volumes.append(volume)

        # Substituir os volumes calculados no laudo_content (em ordêm de ocorrência)
        for volume in volumes:
            laudo_content = laudo_content.replace("x cm³", f"{volume:.2f} cm³", 1)

        print("Novo laudo atualizado:", laudo_content)

        # Atualizar o laudo na sessão
        session["laudo_content"] = laudo_content

        # Retornar o resultado formatado
        return {"output": laudo_content}

    except Exception as e:
        print(f"Erro ao calcular o volume: {e}")
        return {"error": str(e)}

calculo = Tool(
    name="calculadora",
    func=calculo,
    description="Realize os cálculos e insira os resultados nos locais adequados."
)

chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt_gerador = ChatPromptTemplate.from_messages([
    HumanMessage(content=(
        "Você é um assistente que realiza cálculos de volume."
        "Utilize o laudo: {laudo_content}."
        "Quando solicitado, você deve multiplicar os números fornecidos com base na função, atualizar o laudo e retornar o resultado. Envie o resultado final."
        "O cálculo do volume se dá pela multiplicação das dimensões por 0,52."
    ))
])


callback_handler = StdOutCallbackHandler()
agent_calculo = initialize_agent(
    tools=[calculo],
    llm=chat_model,
    agent="zero-shot-react-description",
    handle_parsing_errors=True,
    max_iterations=1,
    callbacks=[callback_handler],
    prompt_template=prompt_gerador
)
