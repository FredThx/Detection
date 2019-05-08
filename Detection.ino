
const int pin_recept = 6;
const int pin_out = 4;
const int pin_buzzer = 13;
const int pin_led_rouge = 2;
const int pin_led_jaune = 3;
const int pin_led_vert = 4;
const int pin_led_bleu = 5;

const long timeout = 5000000; //µsecondes
int valid_signal[] = {1,2,1};//court-long-court
int nb_pulse = 3; //nb de bandes
const float precision = 0.5; // acceptation durées +/- precision%
const long out_duration = 1000; //millisecondes

void setup() {
  pinMode(pin_recept, INPUT);
  pinMode(pin_out, OUTPUT);
  pinMode(pin_led_rouge, OUTPUT);
  pinMode(pin_led_jaune, OUTPUT);
  pinMode(pin_led_bleu, OUTPUT);
  digitalWrite(pin_out,LOW);
  digitalWrite(pin_led_rouge,LOW);
  digitalWrite(pin_led_jaune,LOW);
  digitalWrite(pin_led_bleu,LOW);
  Serial.begin(9600);
  Serial.println("START...");
}

void set_led(int pin_led){
  digitalWrite(pin_led_rouge,LOW);
  digitalWrite(pin_led_jaune,LOW);
  digitalWrite(pin_led_bleu,LOW);
  digitalWrite(pin_led, HIGH);
}

void loop() {
  Serial.println("Attente du signal");
  set_led(pin_led_jaune);
  int i = 0;
  unsigned long durations[nb_pulse];
  do{
    durations[i]=pulseIn(pin_recept,LOW,timeout)/1000;
      Serial.print("Detection (");
      Serial.print(i);
      Serial.print(") : ");
      Serial.println(durations[i]);
      set_led(pin_led_rouge);
    i++;
  }while(durations[i-1] > 0 and i<nb_pulse);
  if (durations[i-1]==0){
    Serial.println("Timeout => Abandon!!!");
  }else{
    Serial.print("Verification signal...");
    i=1;
    bool detect = true;
    do {
      long erreur = durations[i]*valid_signal[0]-durations[0]*valid_signal[i];
      detect = detect and (abs(erreur)< precision * durations[0]);
      i++;
    }while(detect and i<nb_pulse);
    if (detect){
      Serial.println("Detection!!!");
      digitalWrite(pin_out,HIGH);
      tone(pin_buzzer,440);
      delay(out_duration);
      digitalWrite(pin_out,LOW);
      noTone(pin_buzzer);
    }else{
      Serial.println("Mauvais signal => Abandon!!!");
    }
  }
}
