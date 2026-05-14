from flask import Flask, jsonify, render_template_string
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

CHANNEL_ID = "3382097"
BR_TZ = ZoneInfo("America/Sao_Paulo")

# =========================
# HTML COMPLETO
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitoramento IoT</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: Consolas, monospace;
            background: #0f172a;
            color: white;
            text-align: center;
            margin: 0;
            overflow: hidden;
        }

        h1 {
            margin: 20px 0;
        }

        .container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
        }

        .card {
            background: #1e293b;
            margin: 15px;
            padding: 25px;
            border-radius: 10px;
            width: 200px;
        }

        .title {
            color: #94a3b8;
        }

        .value {
            font-size: 1.8em;
            margin-top: 10px;
        }

        /* ÁREA INFERIOR */
        .bottom {
            width: 100%;
            height: calc(100vh - 260px);
            display: flex;
            gap: 20px;
            padding: 20px 40px 30px 40px;
        }

        /* CMD À ESQUERDA */
        .terminal {
            width: 50%;
            height: 100%;
            background: black;
            color: #00ff00;

            padding: 15px;
            border-radius: 10px;

            overflow-x: auto;
            overflow-y: auto;
            white-space: pre;
            text-align: left;
            font-size: 0.9em;

            box-shadow: 0 0 10px rgba(0,0,0,0.5);

            scrollbar-width: thin;
            scrollbar-color: #64748b #020617;
        }

        /* TABELA À DIREITA */
        .table-container {
            width: 50%;
            height: 100%;
            background: #1e293b;

            padding: 15px;
            border-radius: 10px;

            overflow: hidden;
            text-align: left;

            box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }

        .table-scroll {
            width: 100%;
            height: 100%;

            overflow-x: auto;
            overflow-y: auto;

            scrollbar-width: thin;
            scrollbar-color: #64748b #0f172a;
        }

        .terminal::-webkit-scrollbar,
        .table-scroll::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        .terminal::-webkit-scrollbar-track {
            background: #020617;
            border-radius: 10px;
        }

        .table-scroll::-webkit-scrollbar-track {
            background: #0f172a;
            border-radius: 10px;
        }

        .terminal::-webkit-scrollbar-thumb,
        .table-scroll::-webkit-scrollbar-thumb {
            background: #64748b;
            border-radius: 10px;
            border: 2px solid transparent;
            background-clip: content-box;
        }

        .terminal::-webkit-scrollbar-thumb:hover,
        .table-scroll::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
            background-clip: content-box;
        }

        .terminal::-webkit-scrollbar-corner,
        .table-scroll::-webkit-scrollbar-corner {
            background: transparent;
        }

        table {
            width: 100%;
            min-width: 620px;
            border-collapse: collapse;
            color: white;
            font-size: 0.9em;
        }

        thead th {
            position: sticky;
            top: 0;
            background: #334155;
            color: white;
            cursor: pointer;
            padding: 10px;
            text-align: center;
            border-bottom: 1px solid #475569;
            user-select: none;
            z-index: 10;
        }

        tbody td {
            padding: 8px;
            text-align: center;
            border-bottom: 1px solid #334155;
        }

        tbody tr:hover {
            background: #263449;
        }
    </style>
</head>

<body>

<h1>💧 Monitoramento IoT (ThingSpeak)</h1>

<div class="container">
    <div class="card">
        <div class="title">Pressão Raw</div>
        <div class="value" id="f1">--</div>
    </div>

    <div class="card">
        <div class="title">Pressão (MPa)</div>
        <div class="value" id="f2">--</div>
    </div>

    <div class="card">
        <div class="title">Vazão Raw</div>
        <div class="value" id="f3">--</div>
    </div>

    <div class="card">
        <div class="title">Vazão (L/min)</div>
        <div class="value" id="f4">--</div>
    </div>
</div>

<div class="bottom">

    <div class="terminal" id="terminal">&gt; Sistema iniciado...</div>

    <div class="table-container">
        <div class="table-scroll" id="tableContainer">
            <table id="tabela">
                <thead>
                    <tr>
                        <th onclick="ordenarTabela(0)">DataHora ▲▼</th>
                        <th onclick="ordenarTabela(1)">Pressão MPa ▲▼</th>
                        <th onclick="ordenarTabela(2)">Vazão L/min ▲▼</th>
                    </tr>
                </thead>
                <tbody id="corpoTabela">
                </tbody>
            </table>
        </div>
    </div>

</div>

<script>

let registrosCarregados = new Set();
let ordemAsc = true;
let colunaOrdenada = null;

// =============================
// FORMATAÇÃO INTELIGENTE
// =============================
function formatar(valor) {
    let num = Number(valor);
    if (isNaN(num)) return "--";

    return parseFloat(num.toFixed(6)).toString();
}

// =============================
// CARDS SUPERIORES
// =============================
function atualizarCards(item) {
    document.getElementById('f1').innerText = item.f1;
    document.getElementById('f2').innerText = formatar(item.f2);
    document.getElementById('f3').innerText = item.f3;
    document.getElementById('f4').innerText = formatar(item.f4);
}

// =============================
// ORDENAÇÃO DA TABELA
// =============================
function ordenarTabela(coluna) {
    colunaOrdenada = coluna;

    let tabela = document.getElementById("tabela");
    let tbody = tabela.tBodies[0];
    let linhas = Array.from(tbody.rows);

    linhas.sort((a, b) => {
        let valorA = a.cells[coluna].innerText;
        let valorB = b.cells[coluna].innerText;

        if (coluna === 0) {
            valorA = Number(a.cells[coluna].dataset.order);
            valorB = Number(b.cells[coluna].dataset.order);
        }

        if (coluna === 1 || coluna === 2) {
            valorA = Number(valorA);
            valorB = Number(valorB);
        }

        if (valorA < valorB) return ordemAsc ? -1 : 1;
        if (valorA > valorB) return ordemAsc ? 1 : -1;
        return 0;
    });

    ordemAsc = !ordemAsc;

    tbody.innerHTML = "";
    linhas.forEach(linha => tbody.appendChild(linha));
}

// =============================
// REAPLICA ORDENAÇÃO ATUAL
// =============================
function reaplicarOrdenacao() {
    if (colunaOrdenada === null) return;

    let tabela = document.getElementById("tabela");
    let tbody = tabela.tBodies[0];
    let linhas = Array.from(tbody.rows);

    linhas.sort((a, b) => {
        let valorA = a.cells[colunaOrdenada].innerText;
        let valorB = b.cells[colunaOrdenada].innerText;

        if (colunaOrdenada === 0) {
            valorA = Number(a.cells[colunaOrdenada].dataset.order);
            valorB = Number(b.cells[colunaOrdenada].dataset.order);
        }

        if (colunaOrdenada === 1 || colunaOrdenada === 2) {
            valorA = Number(valorA);
            valorB = Number(valorB);
        }

        let ascAtual = !ordemAsc;

        if (valorA < valorB) return ascAtual ? -1 : 1;
        if (valorA > valorB) return ascAtual ? 1 : -1;
        return 0;
    });

    tbody.innerHTML = "";
    linhas.forEach(linha => tbody.appendChild(linha));
}

// =============================
// ADICIONA LINHA NA TABELA
// =============================
function adicionarLinhaTabela(item) {
    let corpoTabela = document.getElementById('corpoTabela');
    let tableContainer = document.getElementById('tableContainer');

    let row = corpoTabela.insertRow();

    let c0 = row.insertCell(0);
    c0.innerText = item.datahora_br;
    c0.dataset.order = item.timestamp_ms;

    row.insertCell(1).innerText = formatar(item.f2);
    row.insertCell(2).innerText = formatar(item.f4);

    reaplicarOrdenacao();

    if (colunaOrdenada === null) {
        tableContainer.scrollTop = tableContainer.scrollHeight;
    }
}

// =============================
// ADICIONA LOG NO CMD
// =============================
function adicionarLogCMD(item) {
    let terminal = document.getElementById('terminal');

    let log = {
        timestamp: item.hora_br,
        status: "OK (Cloud)",
        origem: "ThingSpeak API",
        dados: {
            pressao_raw: item.f1,
            pressao_mpa: formatar(item.f2),
            vazao_raw: item.f3,
            vazao_l_min: formatar(item.f4)
        }
    };

    terminal.innerHTML += "\\n[" + item.hora_br + "] " + JSON.stringify(log);
    terminal.scrollTop = terminal.scrollHeight;
}

// =============================
// CARGA INICIAL DA TABELA
// =============================
function carregarHistoricoTabela() {
    fetch('/api_history')
    .then(res => res.json())
    .then(data => {

        if (!data.feeds) return;

        data.feeds.forEach(item => {
            if (registrosCarregados.has(item.entry_id)) return;

            registrosCarregados.add(item.entry_id);
            adicionarLinhaTabela(item);
        });

        if (data.latest) {
            atualizarCards(data.latest);
        }
    });
}

// =============================
// TEMPO REAL
// =============================
function atualizarTempoReal() {
    fetch('/api')
    .then(res => res.json())
    .then(item => {

        if (!item || !item.entry_id) return;

        atualizarCards(item);

        if (registrosCarregados.has(item.entry_id)) return;

        registrosCarregados.add(item.entry_id);

        adicionarLogCMD(item);
        adicionarLinhaTabela(item);
    });
}

carregarHistoricoTabela();

setInterval(atualizarTempoReal, 4000);
atualizarTempoReal();

</script>

</body>
</html>
"""

# =========================
# FUNÇÕES AUXILIARES
# =========================
def formatar_valor(valor):
    try:
        numero = float(valor)
        texto = f"{numero:.6f}".rstrip("0").rstrip(".")
        return texto if texto else "0"
    except:
        return "--"


def converter_data_br(created_at):
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        dt_br = dt.astimezone(BR_TZ)

        return dt_br.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return "--"


def converter_hora_br(created_at):
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        dt_br = dt.astimezone(BR_TZ)

        return dt_br.strftime("%H:%M:%S")
    except:
        return "--"


def converter_timestamp_ms(created_at):
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except:
        return 0


def normalizar_feed(item):
    created_at = item.get("created_at", "")

    return {
        "entry_id": item.get("entry_id"),
        "datahora_br": converter_data_br(created_at),
        "hora_br": converter_hora_br(created_at),
        "timestamp_ms": converter_timestamp_ms(created_at),
        "f1": formatar_valor(item.get("field1")),
        "f2": formatar_valor(item.get("field2")),
        "f3": formatar_valor(item.get("field3")),
        "f4": formatar_valor(item.get("field4"))
    }


# =========================
# API - ÚLTIMO REGISTRO / TEMPO REAL
# =========================
@app.route('/api')
def api():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results=1"

    try:
        response = requests.get(url)
        data = response.json()

        if "feeds" not in data or len(data["feeds"]) == 0:
            return jsonify({
                "entry_id": None,
                "datahora_br": "--",
                "hora_br": "--",
                "timestamp_ms": 0,
                "f1": "--",
                "f2": "--",
                "f3": "--",
                "f4": "--"
            })

        ultimo = data["feeds"][0]

        return jsonify(normalizar_feed(ultimo))

    except Exception as e:
        print("Erro:", e)

        return jsonify({
            "entry_id": None,
            "datahora_br": "--",
            "hora_br": "--",
            "timestamp_ms": 0,
            "f1": "--",
            "f2": "--",
            "f3": "--",
            "f4": "--"
        })


# =========================
# API - HISTÓRICO DA TABELA
# =========================
@app.route('/api_history')
def api_history():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results=8000"

    try:
        response = requests.get(url)
        data = response.json()

        if "feeds" not in data or len(data["feeds"]) == 0:
            return jsonify({
                "latest": None,
                "feeds": []
            })

        feeds_formatados = [normalizar_feed(item) for item in data["feeds"]]

        return jsonify({
            "latest": feeds_formatados[-1],
            "feeds": feeds_formatados
        })

    except Exception as e:
        print("Erro:", e)

        return jsonify({
            "latest": None,
            "feeds": []
        })


@app.route('/')
def index():
    return render_template_string(HTML)


if __name__ == '__main__':
    app.run(debug=True)