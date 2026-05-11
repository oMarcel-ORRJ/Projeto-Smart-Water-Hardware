#include <SoftwareSerial.h>

// RX no 10 (não usado), TX no 11 (vai para o divisor de tensão e depois pro ESP32)
SoftwareSerial portaESP(10, 11); 

const int PINO_VAZAO = 2; // Pino obrigatório para interrupção no Arduino Uno
volatile int contadorPulsos = 0;
unsigned long tempoAnterior = 0;
const unsigned long intervalo = 5000;

// Função de interrupção (conta os giros da ventoinha do sensor)
void contarPulsos() { 
  contadorPulsos++; 
}

void setup() {
  Serial.begin(115200);
  portaESP.begin(9600); // Canal de comunicação com o ESP32
  
  pinMode(PINO_VAZAO, INPUT_PULLUP); // PULLUP estabiliza o sinal de 5V
  attachInterrupt(digitalPinToInterrupt(PINO_VAZAO), contarPulsos, FALLING);
  
  Serial.println("Arduino: Sistema Iniciado. Contando pulsos...");
}

void loop() {
  unsigned long tempoAtual = millis();

  // Loop executa a cada 5 segundos
  if (tempoAtual - tempoAnterior >= intervalo) {
    tempoAnterior = tempoAtual;

    // Congela a interrupção rapidamente para ler com segurança
    detachInterrupt(digitalPinToInterrupt(PINO_VAZAO));
    int pulsosAtuais = contadorPulsos;
    contadorPulsos = 0;
    attachInterrupt(digitalPinToInterrupt(PINO_VAZAO), contarPulsos, FALLING);

    // Envia o RAW (Pulsos Brutos) para o ESP32 trabalhar
    portaESP.println(pulsosAtuais);
    
    // Log no notebook para você acompanhar
    Serial.print("Pulsos enviados pro ESP32: ");
    Serial.println(pulsosAtuais);
  }
}
