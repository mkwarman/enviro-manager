import RPi.GPIO as GPIO
import serial

arduinoSerialData = serial.Serial('/dev/serial0', 9600)

GPIO.setmode(GPIO.BCM)

MAT_RELAY_PIN = 18
LIGHT_RELAY_PIN = 23

GPIO.setup(MAT_RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LIGHT_RELAY_PIN, GPIO.OUT, initial=GPIO.HIGH)

try:
    while True:
        to_arduino = input("Input data to send to arduino: ")
        arduinoSerialData.write(to_arduino.encode())

except KeyboardInterrupt:
    GPIO.cleanup()
