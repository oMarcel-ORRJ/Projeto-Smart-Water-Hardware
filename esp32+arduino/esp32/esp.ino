#include <ArduinoJson.h>

// Pinos de Comunicação com o Arduino
#define RX2_PIN 16
#define TX2_PIN 17

// Mapeamento de Pinos
const int PINO_PRESSAO = 36;
const int PINO_SWITCH_DEBUG = 5;

void setup() {
  // Inicia a comunicação Serial
  Serial.begin(115200);
  
  // Inicia a comunicação Serial2 (Ouvindo o Arduino)
  Serial2.begin(9600, SERIAL_8N1, RX2_PIN, TX2_PIN);

  pinMode(PINO_PRESSAO, INPUT);
  
  // Configuração do seu Switch de injeção de dados
  pinMode(PINO_SWITCH_DEBUG, INPUT_PULLUP);
  
  Serial.println("ESP32: Aguardando pacotes do Arduino...");
}

void loop() {
  // O ESP32 trabalha SOMENTE quando o Arduino mandar os pulsos!
  if (Serial2.available() > 0) {
    
    // 1. RECEBE OS DADOS
    String dadoRecebido = Serial2.readStringUntil('\n');
    dadoRecebido.trim(); 
    int pulsosAtuais = dadoRecebido.toInt();

    // --- 1. CÁLCULO DA VAZÃO ---
    // Fórmula do Datasheet: Frequência (Hz) = 7.5 * Vazão (L/min)
    // Como nosso intervalo de leitura é de 5 segundos, a Frequência é: pulsos / 5.
    float vazaoLMin = 0.0;
    float frequenciaHz = (float)pulsosAtuais / 5.0;
    vazaoLMin = frequenciaHz / 7.5;

    // --- 2. LEITURA DA PRESSÃO (SIMULADA) ---
    // Teoria: Pressão e vazão são inversamente proporcionais.
    float pressaoMaximaMPa = 0.40;
    float perdaCarga = vazaoLMin * 0.012; // Perde ~0.012 MPa por cada 1 L/min de vazão
    float pressaoAtualMPa = pressaoMaximaMPa - perdaCarga;

    // Impede que a pressão seja negativa
    if (pressaoAtualMPa < 0.0) pressaoAtualMPa = 0.0;

    // Transdutor físico de 1.2MPa envia sinal em tensão, que o ESP converte em Raw (0-4095).
    int pressaoRaw = 620 + (int)((pressaoAtualMPa / 1.2) * 3380);

    // --- 3. HEALTH CHECK E STATUS ---
    String statusSistema = "OK";

    // 1. Modo de injeção de dados para depuração (debug)
    if (digitalRead(PINO_SWITCH_DEBUG) == LOW) {
      statusSistema = "MODO_DEBUG";
    }
    // 2. Anomalia no sensor de vazão: Valores fora do limite físico do YF-S201
    else if (vazaoLMin > 50.0) {
      statusSistema = "ERRO_VAZAO_ANOMALA";
    }

    // --- 4. GERAÇÃO DO JSON ---
    StaticJsonDocument<256> doc; 
    doc["status"] = statusSistema;

    // Popula o JSON baseado no status
    if (statusSistema == "MODO_DEBUG") {
      // MODO DEBUG: Injeta dados realistas simulando uma torneira/chuveiro aberto
      float vazaoDebug = 10.0 + (random(0, 51) / 10.0);
      int pulsosDebug = (int)(vazaoDebug * 7.5 * 5); 

      float pressaoDebugMPa = 0.40 - (vazaoDebug * 0.012) + (random(-5, 6) / 1000.0);
      if (pressaoDebugMPa < 0.0) pressaoDebugMPa = 0.0;
      int pressaoDebugRaw = 620 + (int)((pressaoDebugMPa / 1.2) * 3380);

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
    Serial.println(); 
  }
}
