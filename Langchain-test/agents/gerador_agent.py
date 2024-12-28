from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from unidecode import unidecode
from openai import OpenAI
from dotenv import load_dotenv
from flask import session
import os, re

load_dotenv()

client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY'))
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1oBWgaJkIwHMGV8Dxa2jyQ1p307dsSokMM841vuQvN7g'
CREDENTIALS_FILE = 'laudario-dcd5775bf52c.json'
LOCAL_FILE_PATH = 'data/Prompt4.10.xlsx'

def select_page(phrase, excel_data):
    sheet_names = excel_data.sheet_names
    vectorizer = TfidfVectorizer().fit_transform(sheet_names + [phrase])
    cosine_similarities = cosine_similarity(vectorizer[-1], vectorizer[:-1])
    best_match_idx = cosine_similarities.argmax()
    best_page_name = sheet_names[best_match_idx]
    print(f"page:",best_page_name)
    return excel_data.parse(best_page_name)

def find_closest_row(phrase, data, weight_factor=3, column_a_weight=10):
    phrase = unidecode(phrase)
    def weight_row(row):
        weighted_row = (unidecode(str(row.get('Macro', ''))) + ' ') * column_a_weight
        for col in row.index:
            if col != 'Macro':
                weighted_row += (unidecode(str(row[col])) + ' ') * weight_factor
        return weighted_row
    data_weighted = data.apply(weight_row, axis=1)
    vectorizer = TfidfVectorizer()
    data_vectorized = vectorizer.fit_transform(data_weighted.astype(str))
    phrase_vector = vectorizer.transform([phrase])
    similarity = cosine_similarity(phrase_vector, data_vectorized).flatten()
    closest_index = similarity.argmax()
    print(f"index:",closest_index)
    return closest_index

def find_closest_column(phrase, data):
    phrase = unidecode(phrase)
    headers = [unidecode(col) for col in data.columns]
    vectorizer = TfidfVectorizer()
    headers_vectorized = vectorizer.fit_transform(headers)
    phrase_vector = vectorizer.transform([phrase])
    similarity = cosine_similarity(phrase_vector, headers_vectorized).flatten()
    closest_column_index = similarity.argmax()
    closest_column_name = data.columns[closest_column_index]
    print(f"Column:",closest_column_name)
    return closest_column_name

# API IA model="gpt-4o-mini"
def generate_final_report_with_modifiers(mask_template, raw_modifiers):
    consolidated_modifiers = "\n\n".join(
        f"{phrase}: {template}" for phrase, template in raw_modifiers.items()
    )
    response = client.chat.completions.create( 
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "Você é um gerador de laudo médico que utiliza uma máscara padrão e modificadores específicos para cada caso."},
            {"role": "user",
             "content": f"Utilize os modificadores fornecidos para ajustar a máscara e gerar um laudo final.\n\n"
                        f"Modificadores Ajustados:\n{consolidated_modifiers}\n\n. Insira todos os modificadores na máscara."
                        f"Máscara:\n{mask_template}\n\n."
                        f"Os modificadores ajustados possuem frases que não estão presentes na máscara. Insira essas frases no parágrafro correto da máscara utilizando como referência o local em que estavam nas frases modificadoras."
                        f"Confira se todos os Modificadores Ajustados foram adicionados na máscara. Do contrário, integre-os."
                        f"Evite criar novos textos."
                        f"Elimine do template final as frases contraditórias, dando preferência para as frases com alterações da normalidade."}
        ],
        temperature=0.8,
        max_tokens=2048,
        top_p=0.6,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    # Acessar os atributos do objeto retornado
    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens
    return content, tokens_used

## INPUT Inicial ##
def gerador(input_chat):
    # Debug: Verificar o texto recebido
    print("input_chat:", input_chat)

    # Substituir '//' por '\n' para tratar como quebra de linha
    input_chat = input_chat.replace('//', '\n')
    
    # Dividir o texto por quebras de linha
    phrases = input_chat.splitlines()
    
    # Atribuir frases com base na divisão
    first_phrase = phrases[0].strip() if len(phrases) > 0 else ""
    second_phrase = phrases[1].strip() if len(phrases) > 1 else ""
    key_phrases = []
    for phrase in phrases[2:]:
        key_phrases.extend(phrase.split('\n'))
    key_phrases = [phrase.strip() for phrase in key_phrases if phrase.strip()]
    
    # Debug: Verificar as divisões feitas
    print("First Phrase:", first_phrase)
    print("Second Phrase:", second_phrase)
    print("Key Phrases:", key_phrases)

    file_path = 'data/Prompt4.10.xlsx'
    excel_data = pd.ExcelFile(file_path)
    data_df = select_page(first_phrase, excel_data)

    closest_index = find_closest_row(second_phrase, data_df)
    closest_column_name = find_closest_column(second_phrase, data_df)

    if closest_column_name in data_df.columns and closest_index < len(data_df):
        selected_template = data_df.iat[closest_index, data_df.columns.get_loc(closest_column_name)]
        print("Máscara:", selected_template)
    else:
        return({'error': f"Coluna '{closest_column_name}' ou índice de linha '{closest_index}' não encontrado."})
    
    if not key_phrases:
        selected_template_replaced = selected_template.replace("\n", "<br>")
        formatted_selected_template = f"<p>{selected_template_replaced}</p>"
        ## Envia o laudo gerado para o Word
        laudo_content = formatted_selected_template
        session["laudo_content"] = laudo_content
        return({'template': formatted_selected_template})

    raw_modifiers = {}
    for key_phrase in key_phrases:
        closest_index = find_closest_row(key_phrase, data_df)
        if closest_column_name in data_df.columns and closest_index < len(data_df):
            selected_modifier = data_df.iat[closest_index, data_df.columns.get_loc(closest_column_name)]
            raw_modifiers[key_phrase] = selected_modifier
            print("modificador:", selected_modifier)
        else:
            raw_modifiers[key_phrase] = f"Template não encontrado para {key_phrase}"

    final_report, tokens_used = generate_final_report_with_modifiers(selected_template, raw_modifiers)

    final_report_replaced = final_report.replace("\n", "<br>")
    final_report_replaced = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', final_report_replaced)
    formatted_final_report = f"<p>{final_report_replaced}</p>"
    ## Envia o laudo gerado para o Word
    laudo_content = formatted_final_report
    session["laudo_content"] = laudo_content

    return({'template': formatted_final_report, 'tokens_used': tokens_used})

gerador = Tool(
    name="gerador",
    func=gerador,
    description="Envie a frase separa por // para o gerador. Ao receber o template, envie somente comentários como: laudo gerado."
)

chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt_gerador = ChatPromptTemplate.from_messages([
    HumanMessage(content="Envie a frase separa por // para o gerador. Ao receber o template, envie somente comentários como: laudo gerado.")
])

agent_gerador = initialize_agent(
    tools=[gerador],
    llm=chat_model,
    agent="zero-shot-react-description",
    handle_parsing_errors=True,
    prompt_template=prompt_gerador
)
