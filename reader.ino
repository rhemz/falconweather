volatile int pulse_count = 0;

double interval = 2.0;
int publish_interval = 5;
double readings[5];  // publish_interval not available
int interval_ticker = 0;

double closure_secs = 2.45; // Davis is 2.25
unsigned long lastTime = 0;



void setup() {

    pinMode(D7, OUTPUT);

    pinMode(D1, INPUT_PULLDOWN);

    attachInterrupt(D1, pulseStart, FALLING);
}


void loop() {
    unsigned long now = millis();

	if ((now - lastTime) >= interval * 1000) {

	    // calculate wind mph
	    double result = calculate_mph(pulse_count, interval, closure_secs);
	    readings[interval_ticker] = result;

	    // reset pulses back to 0
        pulse_count = 0;

	    if(interval_ticker == publish_interval - 1) {
	        double avg_reading = average_value(readings);
	        double max_reading = max_value(readings);

	        String fmt = "";
	        // Particle.publish("Wind Speed", fmt.format("%1.1f mph", result).c_str(), PUBLIC);
            // Particle.publish("windmph", String(max_reading).c_str(), PUBLIC);
            Particle.publish("windmph", fmt.format("%1.1f|%2.1f", avg_reading, max_reading).c_str(), PUBLIC);

            // clear readings
            memset(readings, 0.0, sizeof(readings));

            // reset ticker
            interval_ticker = 0;
	    } else {
	        // increment ticker
	        interval_ticker++;
	    }

        lastTime = now;
	}

    delay(1000);
}


void pulseStart() {
    // Interrupt handler
    digitalWrite(D7, HIGH);
    pulse_count++;
}


double calculate_mph(int pulse_count, double interval, double closure_secs) {
    // convert to mp/h using the formula V=P(C/T)
    double result = pulse_count * (closure_secs / interval);

    return result;
}


double max_value(double* values) {
    double max = 0.0;

    for (int i=0; i<sizeof(values); i++) {
        if(values[i] > max) {
            max = values[i];
        }
    }

    return max;
}


double average_value(double* values) {
    double sum = 0.0;

    for(int i=0; i<sizeof(values); i++) {
        sum += values[i];
    }

    return sum / sizeof(values);
}
