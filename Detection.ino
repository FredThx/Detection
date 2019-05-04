
const int pin_recept = 7;
const int pin_out = 2;
const long timeout = 5000000; //µsecondes
int valid_signal[] = {1,2,1};//court-long-court
int nb_pulse = 3; //nb de bandes
const float precision = 0.4; // acceptation durées +/- precision%
const long out_duration = 1000; //millisecondes

void setup() {
  pinMode(pin_recept, INPUT);
  pinMode(pin_out, OUTPUT);
  digitalWrite(pin_out,LOW);
  Serial.begin(9600);
  Serial.println("START...");
}

void loop() {
  Serial.println("Attente du signal");
  int i = 0;
  unsigned long durations[nb_pulse];
  do{
    durations[i]=pulseIn(pin_recept,HIGH,timeout)/1000;
      Serial.print("Detection (");
      Serial.print(i);
      Serial.print(") : ");
      Serial.println(durations[i]);
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
      delay(out_duration);
      digitalWrite(pin_out,LOW);      
    }else{
      Serial.println("Mauvais signal => Abandon!!!");
    }
  }
}
