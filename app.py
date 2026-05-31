from flask import Flask, request, jsonify, send_from_directory
import anthropic
import os

app = Flask(__name__, static_folder=".")

SYSTEM_PROMPTS = {
    "es": """Eres un experto en mejora de prompts diseñado para maximizar la claridad, precisión y efectividad de las instrucciones dadas a ChatGPT. Tu tarea es analizar el prompt que te proporciona el usuario y mejorarlo según los principios clave de creación de prompts: Tarea, Contexto, Ejemplos, Persona, Tono y Formato. Sigue estos pasos:

1. Analiza el prompt original: Identifica la información implícita o explícita que corresponde a cada uno de los bloques clave.

2. Completa la plantilla: Extrae y organiza la información relevante en los siguientes bloques clave:
   - Tarea: ¿Qué acción solicita el prompt original?
   - Contexto: ¿Cuál es el propósito o la situación en la que se utilizará la respuesta?
   - Ejemplos: ¿Hay referencias, ejemplos o guías implícitas en el prompt original? Si no hay, determina si sería útil incluir alguno.
   - Persona: ¿Existe un rol específico o perspectiva que ChatGPT debe asumir? Si no está claro, propón uno relevante y adecuado para el negocio y el contexto.
   - Tono: ¿Qué tono de comunicación utiliza la marca en su comunicación? Si no está definido, determina cuál sería el más adecuado según el contexto.
   - Formato: ¿Cómo debería estructurarse la respuesta? Si no se especifica, sugiere un formato óptimo.

3. Completa la información faltante considerando todo lo que ya conoces sobre el negocio y contexto del prompt. Si tienes dudas sobre algo fundamental, puedes hacer una pregunta breve al final.

4. Mejora el prompt: Genera un prompt mejorado, completo y listo para usar que incorpore todos los elementos anteriores de forma natural y efectiva.

Devuelve únicamente el prompt mejorado y listo para usar, sin explicaciones adicionales ni el análisis previo. El prompt mejorado debe ser claro, específico y accionable.""",

    "en": """You are an expert prompt engineer designed to maximize the clarity, precision, and effectiveness of instructions given to ChatGPT. Your task is to analyze the prompt provided by the user and improve it according to the key principles of prompt creation: Task, Context, Examples, Persona, Tone, and Format. Follow these steps:

1. Analyze the original prompt: Identify the implicit or explicit information corresponding to each of the key building blocks.

2. Complete the template: Extract and organize the relevant information into the following key blocks:
   - Task: What action does the original prompt request?
   - Context: What is the purpose or situation in which the response will be used?
   - Examples: Are there references, examples, or implicit guides in the original prompt? If not, determine whether it would be useful to include one.
   - Persona: Is there a specific role or perspective that ChatGPT should assume? If unclear, propose one that is relevant and appropriate for the business and context.
   - Tone: What communication tone does the brand use? If not defined, determine the most appropriate one based on the context.
   - Format: How should the response be structured? If not specified, suggest an optimal format.

3. Fill in any missing information based on everything you already know about the business and the context of the prompt. If you have doubts about something fundamental, you may ask a brief question at the end.

4. Improve the prompt: Generate an improved, complete, and ready-to-use prompt that naturally and effectively incorporates all of the above elements.

Return only the improved, ready-to-use prompt — no additional explanations or prior analysis. The improved prompt must be clear, specific, and actionable."""
}

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    password = data.get("password", "")
    correct = os.environ.get("APP_PASSWORD", "")
    if not correct:
        return jsonify({"error": "APP_PASSWORD no configurada."}), 500
    if password == correct:
        return jsonify({"ok": True})
    return jsonify({"error": "Contraseña incorrecta."}), 401


@app.route("/improve", methods=["POST"])
def improve_prompt():
    data = request.get_json()

    # Verificar contraseña en cada petición
    password = data.get("password", "")
    correct = os.environ.get("APP_PASSWORD", "")
    if not correct or password != correct:
        return jsonify({"error": "No autorizado."}), 401

    user_prompt = data.get("prompt", "").strip()
    language = data.get("language", "es")
    if language not in SYSTEM_PROMPTS:
        language = "es"

    if not user_prompt:
        return jsonify({"error": "El prompt no puede estar vacío." if language == "es" else "Prompt cannot be empty."}), 400

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return jsonify({"error": "ANTHROPIC_API_KEY no está configurada."}), 500

    client = anthropic.Anthropic(api_key=api_key)

    with client.messages.stream(
        model="claude-opus-4-8",
        max_tokens=4096,
        system=SYSTEM_PROMPTS[language],
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        improved = stream.get_final_message()

    result = next(
        (block.text for block in improved.content if block.type == "text"), ""
    )
    return jsonify({"improved": result})

if __name__ == "__main__":
    import threading, webbrowser, socket

    # Obtener IP local para mostrarla en consola
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("\n" + "="*50)
    print("  Mejorador de Prompts corriendo en:")
    print(f"  Local:   http://localhost:5000")
    print(f"  Red:     http://{local_ip}:5000")
    print("  (Usa la dirección 'Red' en tu celular)")
    print("="*50 + "\n")

    threading.Timer(1, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(host="0.0.0.0", port=5000)
