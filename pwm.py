import RPi.GPIO as GPIO
import therm
from time import sleep

GPIO.setmode(GPIO.BCM)

GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.OUT)

red = GPIO.PWM(24, 100)

red.start(100)

target_upper = 91
target_lower = 89
duty_cycle = 100

poll_delay = 1

#pause_time = 0.02

#cycle_time = (1/60)
#time_off = cycle_time - (0/100)/60

#cross = 0

def fire():
    #print("in fire()")
    #GPIO.output(24, 1)
    sleep(time_off)
    GPIO.output(24, 1)
    sleep(cycle_time-time_off)
    GPIO.output(24, 0)
    return
    #sleep(0.1)

def my_callback(channel):
    global cross
    if cross == 0:
        fire()
        return
    elif cross == 59:
        cross = 0
    else:
        cross += 1
    #print('Edge detected on %s' %channel)
    #red.ChangeFrequency(60)
    #red.start(100)
    #GPIO.remove_event_detect(25)

#GPIO.add_event_detect(25, GPIO.RISING, callback=my_callback)

'''
try:
    while True:
        i = input("input duty cycle: ")
        time_off = cycle_time - (float(i)/100)/60
        print("new time_off: " + str(time_off))
        #red.ChangeDutyCycle(float(i))
        
        for i in range(0,101):
            red.ChangeDutyCycle(i)
            sleep(pause_time)
        for i in range(100,-1,-1):
            red.ChangeDutyCycle(i)
            sleep(pause_time)
        
'''
try:
    while True:
        temp = float(therm.get_temp("f"))
        print("\nCurrent temp: " + str(temp))
        if temp < target_lower and duty_cycle < 100:
            duty_cycle += 5
            print("Increasing... New duty_cycle: " + str(duty_cycle))
        elif temp > target_upper and duty_cycle > 0:
            duty_cycle -= 5
            print("Decreasing... New duty_cycle: " + str(duty_cycle))
        else:
            print("No change... duty_cycle: " + str(duty_cycle))
        red.ChangeDutyCycle(duty_cycle)
        
        sleep(poll_delay)

except:
    red.stop(24)
    #GPIO.remove_event_detect(25)
    GPIO.cleanup()
