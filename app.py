from flask import Flask, request
import requests

app = Flask(__name__)

import os
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
SUBDOMINIO = os.getenv("SUBDOMINIO")
CAMPO_CONTADOR = os.getenv("CAMPO_CONTADOR")
CAMPO_TOTAL = os.getenv("CAMPO_TOTAL")

@app.after_request
def set_default_content_type(response):
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        headers = dict(request.headers)
        raw_data = request.get_data(as_text=True)
        
        print("🔔 Headers recibidos:", headers)
        print("📦 Cuerpo crudo recibido:", raw_data)

        data = request.get_json(force=True)

        print("📘 JSON parseado:", data)

        leads = data.get("leads", {}).get("add", [])
        for lead in leads:
            lead_id = lead["id"]

            r = requests.get(
                f"https://{SUBDOMINIO}.kommo.com/api/v4/leads/{lead_id}",
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            )
            lead_data = r.json()
            campos = lead_data.get("custom_fields_values", [])

            valor_actual = 0
            for campo in campos:
                if str(campo["field_id"]) == CAMPO_CONTADOR:
                    try:
                        valor_actual = int(campo["values"][0]["value"])
                    except:
                        valor_actual = 0
                    break

            nuevo_valor = valor_actual + 1

            payload = {
                "custom_fields_values": [
                    {
                        "field_id": int(CAMPO_TOTAL),
                        "values": [{"value": nuevo_valor}]
                    }
                ]
            }

            requests.patch(
                f"https://{SUBDOMINIO}.kommo.com/api/v4/leads/{lead_id}",
                headers={
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

        return {"status": "ok"}, 200
    
    except Exception as e:
        print("❌ Error procesando webhook:", str(e))
        return {"error": "Error procesando webhook", "details": str(e)}, 500



@app.route("/", methods=["GET"])
def home():
    return jsonify({"mensaje": "Webhook Kommo activo"}), 200



if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # <- ¡clave para Railway!
    app.run(host="0.0.0.0", port=port)
