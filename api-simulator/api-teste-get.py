from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

CHANNEL_ID = "3382097"

# =========================
# HTML COMPLETO
# =========================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Monitoramento IoT</title>

    <style>
        body {
            font-family: Consolas, monospace;
            background: #0f172a;
            color: white;
            text-align: center;
            margin: 0;
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
            justify-content: center;
            padding: 20px 40px 30px 40px; /* ✅ lateral simétrico + bottom */
            box-sizing: border-box;
        }

        /* TERMINAL CENTRALIZADO */
        .terminal {
            width: 100%;
            max-width: 1400px;

            height: 100%;
            background: black;
            color: #00ff00;

            padding: 15px;
            border-radius: 10px;

            overflow-y: auto;
            text-align: left;
            font-size: 0.9em;

            box-shadow: 0 0 10px rgba(0,0,0,0.5);
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
    <div class="terminal" id="terminal">
        &gt; Sistema iniciado...
        <br>
        <br>
    </div>
</div>

<script>

// =============================
// FORMATAÇÃO INTELIGENTE
// =============================
function formatar(valor) {
    let num = Number(valor);
    if (isNaN(num)) return "--";

    // até 6 casas, removendo zeros desnecessários
    return parseFloat(num.toFixed(6)).toString();
}

// =============================
// ATUALIZAÇÃO
// =============================
function atualizar() {
    fetch('/api')
    .then(res => res.json())
    .then(data => {

        // → Atualiza cards (com formatação)
        document.getElementById('f1').innerText = data.f1;
        document.getElementById('f2').innerText = formatar(data.f2);
        document.getElementById('f3').innerText = data.f3;
        document.getElementById('f4').innerText = formatar(data.f4);

        // → Terminal
        let terminal = document.getElementById('terminal');
        let timestamp = new Date().toLocaleTimeString();

        let log = {
            timestamp: timestamp,
            status: "OK (Cloud)",
            origem: "ThingSpeak API",
            dados: {
                pressao_raw: Number(data.f1),
                pressao_mpa: Number(data.f2),
                vazao_raw: Number(data.f3),
                vazao_l_min: Number(data.f4)
            }
        };

        let linha = `[${timestamp}] ${JSON.stringify(log)}`;

        terminal.innerHTML += linha + "<br>";
        terminal.scrollTop = terminal.scrollHeight;
    });
}

// Atualiza a cada 4s
setInterval(atualizar, 4000);
atualizar();

</script>

</body>
</html>
"""

# =========================
# API
# =========================
@app.route('/api')
def api():
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?results=1"

    try:
        response = requests.get(url)
        data = response.json()

        if "feeds" not in data or len(data["feeds"]) == 0:
            return jsonify({"f1": "--", "f2": "--", "f3": "--", "f4": "--"})

        ultimo = data["feeds"][0]

        return jsonify({
            "f1": ultimo.get("field1", "--"),
            "f2": ultimo.get("field2", "--"),
            "f3": ultimo.get("field3", "--"),
            "f4": ultimo.get("field4", "--")
        })

    except Exception as e:
        print("Erro:", e)
        return jsonify({"f1": "--", "f2": "--", "f3": "--", "f4": "--"})

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(debug=True)