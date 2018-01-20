import serial
arduinoSerialData = serial.Serial('/dev/serial0', 9600)

while 1:
    delay = input("Input delay: ")
    arduinoSerialData.write(delay.encode())
