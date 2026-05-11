from flask import Flask, jsonify, render_template_string
import serial
import serial.tools.list_ports
import threading
import json
import time

app = Flask(__name__)

dados_atuais = {
    "status": "AGUARDANDO DADOS...",
    "vazao_l_min": 0.0,
    "pressao_mpa": 0.0,
    "pressao_raw": 0
}
linhas_console = ["Aguardando conexão com o ESP32..."]

# ==========================================
# CONFIGURAÇÃO DA PORTA SERIAL
# No Linux: '/dev/ttyUSB0' ou '/dev/ttyACM0'
# No Windows: 'COM3', 'COM4', etc.
# ==========================================
PORTA_SERIAL = '/dev/ttyACM1'  
BAUD_RATE = 115200

def listar_portas_disponiveis():
    portas = serial.tools.list_ports.comports()
    print("\n" + "="*50)
    print("PORTAS USB DETECTADAS NO COMPUTADOR:")
    if not portas:
        print("Nenhuma porta encontrada! Verifique o cabo.")
    for p in portas:
        print(f"    {p.device} - {p.description}")
    print("="*50 + "\n")

def ler_serial():
    global dados_atuais, linhas_console
    
    while True:
        try:
            ser = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
            linhas_console.append(f"> Conectado à porta {PORTA_SERIAL} com sucesso!")
            
            while True:
                if ser.in_waiting > 0:
                    linha_bytes = ser.readline()
                    try:
                        linha_str = linha_bytes.decode('utf-8').strip()
                        if linha_str:
                            linhas_console.append(linha_str)
                            if len(linhas_console) > 30:
                                linhas_console.pop(0)

                            if linha_str.startswith('{') and linha_str.endswith('}'):
                                json_recebido = json.loads(linha_str)
                                dados_atuais.update(json_recebido)
                    except Exception as e:
                        pass
        except serial.SerialException:
            erro_msg = f"> ERRO: Não foi possível abrir {PORTA_SERIAL}. Tentando novamente..."
            if linhas_console[-1] != erro_msg:
                linhas_console.append(erro_msg)
            time.sleep(3)

# Roda o mapeamento de portas assim que o script inicia!
listar_portas_disponiveis()

thread_serial = threading.Thread(target=ler_serial, daemon=True)
thread_serial.start()

# --- HTML E CSS DA PÁGINA ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitoramento de Fluidos</title>
    <style>
        :root {
            --bg-color: #0b0c10;
            --card-bg: #1f2833;
            --text-main: #c5c6c7;
            --accent-purple: #9d4edd;
            --neon-green: #66fcf1;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            height: 95vh;
            box-sizing: border-box;
        }
        .dashboard {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 20px;
            margin-top: 10px;
        }
        .card {
            background-color: var(--card-bg);
            border-top: 4px solid var(--accent-purple);
            border-radius: 8px;
            padding: 20px;
            flex: 1;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .card-title {
            font-size: 1.1rem;
            color: #8a8d91;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .card-value {
            font-size: 3.5rem;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 5px;
        }
        .unit { font-size: 1.5rem; color: var(--accent-purple); font-weight: normal; }
        
        .raw-data {
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            color: #6c757d;
            background: rgba(0,0,0,0.2);
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
            margin: 0 auto;
        }

        .status-ok { color: var(--neon-green); text-shadow: 0 0 10px rgba(102, 252, 241, 0.5); font-size: 2.8rem;}
        .status-alert { color: #ff003c; text-shadow: 0 0 10px rgba(255, 0, 60, 0.5); font-size: 2.2rem;}
        .status-debug { color: #fca311; font-size: 2.5rem;}
        
        .console-container {
            flex: 1;
            background-color: #000000;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            /* Limita a altura para forçar a barra de rolagem a aparecer internamente */
            max-height: calc(100vh - 240px);
        }
        .console-header {
            color: #8a8d91;
            font-size: 0.9rem;
            margin-bottom: 10px;
            border-bottom: 1px solid #333;
            padding-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .console-output {
            flex: 1;
            overflow-y: scroll; /* Força a barra de rolagem */
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.95rem;
            color: var(--neon-green);
            line-height: 1.4;
            padding-right: 5px;
        }
        
        /* Estilização da barra de rolagem para combinar com o tema dark */
        .console-output::-webkit-scrollbar {
            width: 8px;
        }
        .console-output::-webkit-scrollbar-track {
            background: #0a0a0a; 
            border-radius: 4px;
        }
        .console-output::-webkit-scrollbar-thumb {
            background: #333333; 
            border-radius: 4px;
        }
        .console-output::-webkit-scrollbar-thumb:hover {
            background: var(--accent-purple); 
        }
    </style>
</head>
<body>

    <div class="dashboard">
        <div class="card">
            <div class="card-title">Status do Sistema</div>
            <div class="card-value" id="ui_status" style="margin-bottom: 15px;">-</div>
            <div class="raw-data">SYSTEM_HEALTH_CHECK</div>
        </div>
        <div class="card">
            <div class="card-title">Vazão</div>
            <div class="card-value"><span id="ui_vazao">0.00</span> <span class="unit">L/min</span></div>
            <div class="raw-data">RAW: <span id="ui_vazao_raw">0</span> pulsos</div>
        </div>
        <div class="card">
            <div class="card-title">Pressão da Linha</div>
            <div class="card-value"><span id="ui_pressao">0.000</span> <span class="unit">MPa</span></div>
            <div class="raw-data">RAW: <span id="ui_pressao_raw">0</span> ADC</div>
        </div>
    </div>

    <div class="console-container">
        <div class="console-header">TERMINAL</div>
        <div class="console-output" id="ui_console"></div>
    </div>

    <script>
        function atualizarDados() {
            fetch('/api/dados')
                .then(response => response.json())
                .then(data => {
                    // Atualiza Painéis Principais
                    document.getElementById('ui_vazao').innerText = data.atual.vazao_l_min.toFixed(2);
                    document.getElementById('ui_pressao').innerText = data.atual.pressao_mpa.toFixed(3);
                    
                    // Atualiza os dados RAW
                    document.getElementById('ui_vazao_raw').innerText = data.atual.vazao_raw || 0;
                    document.getElementById('ui_pressao_raw').innerText = data.atual.pressao_raw || 0;
                    
                    let statusEl = document.getElementById('ui_status');
                    statusEl.innerText = data.atual.status;
                    
                    // Tratamento de Cores do Status
                    statusEl.className = "card-value"; 
                    if(data.atual.status === "OK") {
                        statusEl.classList.add("status-ok");
                    } else if(data.atual.status === "MODO_DEBUG") {
                        statusEl.classList.add("status-debug");
                    } else {
                        statusEl.classList.add("status-alert");
                    }

                    // Atualiza Console
                    let consoleEl = document.getElementById('ui_console');
                    consoleEl.innerHTML = data.console.join('<br>');
                    
                    // Força o scroll automático para o final
                    consoleEl.scrollTop = consoleEl.scrollHeight;
                })
                .catch(error => console.error('Erro ao buscar dados:', error));
        }

        setInterval(atualizarDados, 1000);
        atualizarDados(); 
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/dados')
def api_dados():
    # Retorna o pacote completo para o Javascript
    return jsonify({
        "atual": dados_atuais,
        "console": linhas_console
    })

if __name__ == '__main__':
    # Roda o servidor local na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=False)
