
#include <ESP8266WiFi.h>

#define SSID      "Conker"
#define PASSWORD  "2mais2=Quatro"
#define HOST_IP   "192.168.1.103"
#define HOST_PORT 9999

#define INPUT_SR04_PIN 4
#define OUTPUT_SR04_PIN 12


WiFiClient client;
unsigned long now;
uint16_t limMin, limMax;
uint8_t outsideLimit = 0;

void connectToWifi()
{
  Serial.print("Connecting to ");
  Serial.println(SSID);
  
  WiFi.begin(SSID, PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());  
}

uint8_t connectToHost()
{
  if(WiFi.status() != WL_CONNECTED) {
    connectToWifi();
  }
  if (!client.connect(HOST_IP, HOST_PORT)) {
    Serial.println("connection failed");
    return 0;
  } else {
    Serial.println("Connected to Host");
    return 1;
  }
}

uint8_t sendData(uint8_t *buff)
{
  char response[4];
  uint8_t responseCntr = 0;
  if(!client.connected())
  {
    Serial.println("Host not available");
    if(!connectToHost())
    {
      Serial.println("Coudn't connect to host");
      return 0;
    }
  }
  client.flush();
  client.write((const uint8_t *)buff, 6);

  /*Check if the server responded*/
  while(client.available() != 0)
  {
    if(responseCntr < 4)
    {
      response[responseCntr++] = client.read();
    } else {
      responseCntr++;
    }
  }
  if(responseCntr == 4)
  {
    /*The first 2 bytes are the min*/
    memcpy(&limMin, response, 2);
    /*The last 2 bytes are the max*/
    memcpy(&limMax, &response[2], 2);
    Serial.println(limMin);
    Serial.println(limMax);
  }
  Serial.println("Data Send");
  return 1;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(INPUT_SR04_PIN, INPUT);
  pinMode(OUTPUT_SR04_PIN, OUTPUT);
  delay(10);
  now = millis();
  limMin = 0;
  limMax = 65535;
}

void loop() {
  long duration = 0;
  uint16_t sendTime;
  uint8_t i;
  for(i = 0; i < 5; i++)
  {
    digitalWrite(OUTPUT_SR04_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(OUTPUT_SR04_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(OUTPUT_SR04_PIN, LOW);
    duration += pulseIn(INPUT_SR04_PIN, HIGH);
    delay(10);
  }
  duration /= 5;
  if(duration < limMin || duration > limMax)
  { 
    /*If it is outside the limit*/
    if(outsideLimit)
    {
      /*If it was already outside the limit just send message at long intervals*/
      sendTime = 5000;
    } else {
      /*if this is the first outside the limit */
      outsideLimit = 1;
      sendTime = 100;
    }
  } else {
    if(outsideLimit)
    {
      /*if this is the stateChange bring the sendTime to 0*/
      outsideLimit = 0;
      sendTime = 100;
    } else {
      sendTime = 5000;
    }
  }
  /*If it is time to send*/
  if ((millis() - now) > sendTime || now > millis())
  {
    Serial.println(duration);
    /*First generate the buffer*/
    uint32_t id = ESP.getChipId();
    uint16_t val = duration; /*Its limit is around 5000 so it is ok to confine it in 16bits*/
    uint8_t data[6]; 
    memcpy(data,&id,4);
    memcpy(&data[4],&val,2);

    sendData(data);
    now = millis();
  }
}
