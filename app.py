from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

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
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = request.get_json()
        elif 'application/x-www-form-urlencoded' in content_type:
            # Convierte los datos codificados en una estructura similar a JSON
            form_data = request.form.to_dict(flat=False)
            # Necesitamos desanidar el formato: leads[add][0][id]
            lead_ids = []
            for key, values in form_data.items():
                if key.startswith("leads[add]") and key.endswith("[id]"):
                    lead_ids.extend(values)
            data = {"leads": {"add": [{"id": int(lead_id)} for lead_id in lead_ids]}}
        else:
            return jsonify({"error": "Unsupported Content-Type"}), 415

        leads = data.get("leads", {}).get("add", [])
        for lead in leads:
            lead_id = lead["id"]
            # Obtener el lead completo
            r = requests.get(
                f"https://{SUBDOMINIO}.kommo.com/api/v4/leads/{lead_id}",
                headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
            )
            lead_data = r.json()
            campos = lead_data.get("custom_fields_values", [])

            # Buscar el valor del campo contador
            valor_actual = 0
            for campo in campos:
                if str(campo["field_id"]) == CAMPO_CONTADOR:
                    try:
                        valor_actual = int(campo["values"][0]["value"])
                    except:
                        valor_actual = 0
                    break

            nuevo_valor = valor_actual + 1

            # Preparar actualización
            payload = {
                "custom_fields_values": [
                    {
                        "field_id": int(CAMPO_TOTAL),
                        "values": [{"value": nuevo_valor}]
                    }
                ]
            }

            # Enviar actualización al lead
            requests.patch(
                f"https://{SUBDOMINIO}.kommo.com/api/v4/leads/{lead_id}",
                headers={
                    "Authorization": f"Bearer {ACCESS_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=payload
            )

        return jsonify({"status": "OK"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({"mensaje": "Webhook Kommo activo"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
