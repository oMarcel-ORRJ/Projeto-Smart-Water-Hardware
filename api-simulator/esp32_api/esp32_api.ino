#include <ArduinoJson.h>
#include <WiFi.h>
#include <HTTPClient.h>

// Config comunicação
const char* ssid = "REDE-WIFI";
const char* password = "SENHA-WIFI";

String apiKey = "KF8CZKCR2RV3FZVC";

// Debug por variável
bool DEBUG_MODE = true;

// Mapeamento de Pinos
const int PINO_PRESSAO = 36;
const int PINO_VAZAO = 14;
const int PINO_SWITCH_DEBUG = 5;

// Variáveis para o Sensor de Vazão (YF-S201)
volatile int contadorPulsos = 0;
float vazaoLMin = 0.0;

// Temporização de 5 segundos
unsigned long tempoAnterior = 0;
const unsigned long intervalo = 5000;

// Função de interrupção (conta os giros da ventoinha do sensor)
void IRAM_ATTR contarPulsos() { contadorPulsos++; }

void setup() {
  // Inicia a comunicação Serial (Virtual Terminal)
  Serial.begin(115200);

  pinMode(PINO_PRESSAO, INPUT);
  pinMode(PINO_VAZAO, INPUT);

  // Interrupção para ler os pulsos de dados do sensor de vazão
  attachInterrupt(digitalPinToInterrupt(PINO_VAZAO), contarPulsos, FALLING);

  // Configuração do seu Switch de injeção de dados
  pinMode(PINO_SWITCH_DEBUG, INPUT_PULLUP);

  // WiFi
  WiFi.begin(ssid, password);

  Serial.print("Conectando WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi conectado!");
}

void loop() {
  unsigned long tempoAtual = millis();

  // Loop executa a cada 5 segundos
  if (tempoAtual - tempoAnterior >= intervalo) {
    tempoAnterior = tempoAtual;

    // --- 1. CÁLCULO DA VAZÃO ---
    detachInterrupt(digitalPinToInterrupt(PINO_VAZAO));
    int pulsosAtuais = contadorPulsos;
    contadorPulsos = 0;
    attachInterrupt(digitalPinToInterrupt(PINO_VAZAO), contarPulsos, FALLING);

    // Fórmula do Datasheet: Frequência (Hz) = 7.5 * Vazão (L/min)
    // Como nosso intervalo de leitura é de 5 segundos, a Frequência é: pulsos
    // / 5.
    float frequenciaHz = (float)pulsosAtuais / 5.0;
    vazaoLMin = frequenciaHz / 7.5;

    // --- 2. LEITURA DA PRESSÃO (SIMULADA) ---
    // Teoria: Pressão e vazão são inversamente proporcionais.
    // Assumimos que a pressão máxima na rede (com fluxo 0) é de ~0.40 MPa (40
    // m.c.a). Quando a água flui, a pressão na linha cai proporcionalmente à
    // vazão.
    float pressaoMaximaMPa = 0.40;
    float perdaCarga =
        vazaoLMin * 0.012; // Perde ~0.012 MPa por cada 1 L/min de vazão
    float pressaoAtualMPa = pressaoMaximaMPa - perdaCarga;

    // Impede que a pressão seja negativa
    if (pressaoAtualMPa < 0.0)
      pressaoAtualMPa = 0.0;

    // Transdutor físico de 1.2MPa envia sinal em tensão, que o ESP converte em
    // Raw (0-4095). 0 MPa costuma ter um offset de tensão (ex: ~620 no ADC). O
    // topo do range sobe linearmente.
    int pressaoRaw = 620 + (int)((pressaoAtualMPa / 1.2) * 3380);

    // --- 3. HEALTH CHECK E STATUS ---
    String statusSistema = "OK";

    // 1. Modo de injeção de dados para depuração (debug)
    if (DEBUG_MODE || digitalRead(PINO_SWITCH_DEBUG) == LOW) {
      statusSistema = "MODO_DEBUG";
    }
    // 2. Anomalia no sensor de vazão: Valores fora do limite físico do YF-S201
    // O sensor suporta no máximo ~30 L/min. Acima de 50, é provável que seja
    // ruído elétrico ou curto.
    else if (vazaoLMin > 50.0) {
      statusSistema = "ERRO_VAZAO_ANOMALA";
    }
    // 3. Anomalia de Pressão (Lógica para quando tiverem o hardware real):
    // Transdutores começam em ~0.5V (Raw ~620). Se o pino ler 0 absoluto (0V),
    // o fio rompeu/desconectou. int leituraPressaoFisica =
    // analogRead(PINO_PRESSAO); else if (leituraPressaoFisica <= 10 ||
    // leituraPressaoFisica >= 4090) {
    //   statusSistema = "ERRO_PRESSAO_DESCONECTADA";
    // }

    // --- 4. GERAÇÃO DO JSON ---
    StaticJsonDocument<256>
        doc; // Tamanho aumentado para comportar o campo status com segurança
    doc["status"] = statusSistema;

    // Declarar variáveis
    int pressaoDebugRaw;
    float pressaoDebugMPa;

    int pulsosDebug;
    float vazaoDebug;

    // Popula o JSON baseado no status
    if (statusSistema == "MODO_DEBUG") {
      // MODO DEBUG: Injeta dados realistas simulando uma torneira/chuveiro
      // aberto Vazão oscilando levemente entre 10.0 e 15.0 L/min
      vazaoDebug = 10.0 + (random(0, 51) / 10.0);
      pulsosDebug = (int)(vazaoDebug * 7.5 * 5); // Reverte a fórmula para achar os pulsos

      // Pressão reage à vazão com uma pequena oscilação (ruído de rede de +-
      // 0.005 MPa)
      pressaoDebugMPa = 0.40 - (vazaoDebug * 0.012) + (random(-5, 6) / 1000.0);
      if (pressaoDebugMPa < 0.0)
        pressaoDebugMPa = 0.0;
      
        pressaoDebugRaw = 620 + (int)((pressaoDebugMPa / 1.2) * 3380);

        doc["pressao_raw"] = pressaoDebugRaw;
        doc["pressao_mpa"] = pressaoDebugMPa;
        doc["vazao_raw"] = pulsosDebug;
        doc["vazao_l_min"] = vazaoDebug;
      } else {
        doc["pressao_raw"] = pressaoRaw;
        doc["pressao_mpa"] = pressaoAtualMPa;
        doc["vazao_raw"] = pulsosAtuais;
        doc["vazao_l_min"] = vazaoLMin;
      }

    // Converte os dados para o formato JSON e envia para a tela (TX)
    serializeJson(doc, Serial);
    Serial.println(); // Pula uma linha para o próximo JSON ficar embaixo

    // Envio ThingSpeak
    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;

      String url = "http://api.thingspeak.com/update?api_key=" + apiKey +
                  "&field1=" + String(pressaoDebugRaw) +
                  "&field2=" + String(pressaoDebugMPa) +
                  "&field3=" + String(pulsosDebug) +
                  "&field4=" + String(vazaoDebug);

      http.begin(url);

      int httpCode = http.GET();

      Serial.print("HTTP enviado: ");
      Serial.println(httpCode);

      http.end();
    }
  }
}
