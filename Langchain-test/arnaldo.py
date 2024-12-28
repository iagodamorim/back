from flask import Flask, render_template, request, jsonify, session
from agents import agent_calculo, agent_gerador
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from unidecode import unidecode
from dotenv import load_dotenv
import openai
import os

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1oBWgaJkIwHMGV8Dxa2jyQ1p307dsSokMM841vuQvN7g'
CREDENTIALS_FILE = 'laudario-dcd5775bf52c.json'
LOCAL_FILE_PATH = 'data/Prompt4.10.xlsx'

app = Flask(__name__)

def fetch_google_sheets_data(spreadsheet_id, credentials_file):
    """Fetches all data from all sheets of a Google Sheets spreadsheet."""
    credentials = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_names = [sheet['properties']['title'] for sheet in sheet_metadata['sheets']]
    data = {}
    for sheet_name in sheet_names:
        sheet_data = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=sheet_name
        ).execute()
        values = sheet_data.get('values', [])
        data[sheet_name] = values
    return data

def save_sheet_to_excel(data, file_path):
    """Saves fetched Google Sheets data to a local Excel file."""
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for sheet_name, values in data.items():
            df = pd.DataFrame(values)
            df.to_excel(writer, index=False, header=False, sheet_name=sheet_name)

# Orquestrador
def orchestrator(chat_content,laudo_content,input_data):
    if "calcule" in chat_content.lower():
        result = agent_calculo.invoke({"input": input_data})
    elif "gerar" in chat_content.lower():
        result = agent_gerador.invoke({"input": chat_content})
    else:
        return "Não identifiquei o agente."

    # Certifique-se de retornar apenas o conteúdo de interesse
    if isinstance(result, dict):
        if "output" in result:
            return result["output"]
        elif "error" in result:
            return f"Erro: {result['error']}"
    elif isinstance(result, str):
        return result  # Retornar diretamente a string
    else:
        return str(result) 
    
@app.route("/")
def home():
    # Fetch data from Google Sheets
    sheets_data = fetch_google_sheets_data(SPREADSHEET_ID, CREDENTIALS_FILE)    
    # Save to local Excel file
    save_sheet_to_excel(sheets_data, LOCAL_FILE_PATH)
    return render_template("index.html")

app.secret_key = "chave_secreta_para_session"
@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    chat_message = data.get("chat", []) # Recebe todas as mensagens do chat
    chat_content = str(chat_message[-1]) # Seleciona a última mensagem enviada no chat
    laudo_content = data.get("textField", "")
    input_data = {"laudo": laudo_content,"chat":chat_content}
    print("input:",input_data)

    #Salvar conteúdos para uso
    session['laudo_content'] = data.get("textField", "")
    session['chat_content'] = data.get("chat", "")

    try:
        response_content = orchestrator(chat_content,laudo_content,input_data)
        laudo_content = session.get("laudo_content", "Sem laudo na sessão")
        return jsonify({
            "response": response_content,  # Exibe no chat
            "updatedTextField": laudo_content  # Atualiza o campo de texto editável
        })
    except Exception as e:
        print("Erro ao processar:", e)
        return jsonify({"error": "Erro ao processar a solicitação"}), 500
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
