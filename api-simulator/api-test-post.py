import requests
import time
import random
import json

API_KEY = "KF8CZKCR2RV3FZVC"

DEBUG_MODE = True
INTERVALO = 15  # segundos

def calcular_pressao(vazao):
    pressao = 0.40 - (vazao * 0.012)
    return max(pressao, 0.0)

def formatar(num):
    return float(f"{num:.6f}")

while True:

    statusSistema = "OK"

    if DEBUG_MODE:
        statusSistema = "MODO_DEBUG"

    if statusSistema == "MODO_DEBUG":

        vazao = 10.0 + (random.randint(0, 50) / 10.0)
        vazao = formatar(vazao)

        pulsos = int(vazao * 7.5 * 5)

        pressao = calcular_pressao(vazao)
        pressao += (random.randint(-5, 5) / 1000.0)
        pressao = formatar(pressao)

        if pressao < 0:
            pressao = 0

        pressao_raw = int(620 + (pressao / 1.2) * 3380)

    else:
        vazao = 0
        pressao = 0
        pulsos = 0
        pressao_raw = 0

    dados = {
        "status": statusSistema,
        "pressao_raw": pressao_raw,
        "pressao_mpa": pressao,
        "vazao_raw": pulsos,
        "vazao_l_min": vazao
    }

    print(json.dumps(dados, indent=2))

    url = (
        f"https://api.thingspeak.com/update"
        f"?api_key={API_KEY}"
        f"&field1={pressao_raw}"
        f"&field2={pressao}"
        f"&field3={pulsos}"
        f"&field4={vazao}"
    )

    print("Enviando para ThingSpeak...")
    print(url)

    response = requests.get(url)

    print("HTTP response:", response.status_code)
    print("-" * 40)

    time.sleep(INTERVALO)