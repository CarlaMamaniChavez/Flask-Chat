from flask import Flask, render_template, request, jsonify
from markupsafe import Markup
import os
import markdown
import logging
from openai import AzureOpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

#Credenciales Modelo o4-mini
endpoint =  os.getenv("ENDPOINT")
model_name = "o4-mini"
deployment = "o4-mini"

subscription_key = os.getenv("KEY")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

#Credenciales Modelo gpt-40-mini
gptmodelEndpoint = os.getenv("modelo2Endpoint")
gptmodelKey = os.getenv("modelo2Key")
gptmodel_model_name = "gpt-4o-mini"
gptmodel_deployment = "gpt-4o-mini"
api_version = "2025-01-01-preview"

clientGen = ChatCompletionsClient(
    endpoint=gptmodelEndpoint,
    credential=AzureKeyCredential(gptmodelKey),
    
)

# Configura el logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("chat.log"),
        logging.StreamHandler()  # también lo muestra en la consola
    ]
)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json.get("message")
    response = client.chat.completions.create(
        messages=[
        {
            "role": "system",
            "content": "Eres un asistente virtual llamado Salomon Tu Amigo, un experto en contabilidad e impuestos nacionales de Bolivia. Tu objetivo principal es responder preguntas de manera precisa, clara y concisa, brindando información útil y actualizada sobre las regulaciones contables y fiscales vigentes en Bolivia.",
        },
        {
            "role": "user",
            "content": user_input,
        }
    ],
    max_completion_tokens=100000,
    model=deployment    
    )

    
    # Aquí simulas una respuesta
    markdown_response = response.choices[0].message.content

    # ✅ Convierte a HTML seguro y marcado
    html_response = Markup(markdown.markdown(markdown_response))

    response = f"{html_response}"
    logging.info(f"Usuario preguntó: {user_input}")
    logging.info(f"Bot Respondio: {response}")
    return jsonify({"answer": response})

@app.route("/suggest", methods=["POST"])
def suggest():
    entrada = request.json.get("message")

    responseGen = clientGen.complete(
    messages=[
        SystemMessage(content="Tu rol es solo sugerencias de preguntas con respecto a la entrada el usuario"),
        UserMessage(content=entrada),
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model=model_name
    )


    sugerencias = responseGen.choices[0].message.content
    logging.info(f"Preguntas sugeridas son: {sugerencias}")

    # Convertir texto a lista de preguntas (por salto de línea)
    lineas = [line.strip("•1234567890.- ") for line in sugerencias.split('\n') if line.strip()]
    top_preguntas = lineas[:5]  # limitar a 5 máximo por seguridad

    return jsonify({"suggested_options": top_preguntas})


if __name__ == "__main__":
    app.run(debug=True)
