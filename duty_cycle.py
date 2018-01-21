import serial

DUTY_CYCLE_MIN = 10
DUTY_CYCLE_MAX = 480

class DutyCycle:
    # Initial value 50%
    duty_cycle = 250
    duty_cycle_delta = 20
    fine_duty_cycle_delta = 1

    def __init__(self, identifier):
        self.identifier = identifier


    def send_to_arduino(self, serialConnection):
        value_string = str(self.duty_cycle)
        while len(value_string) < 3:
            value_string = "0" + value_string

        data = self.identifier + value_string
        print("Sending to arduino: \"" + data + "\"")
        serialConnection.write(data.encode())

    def increase_duty_cycle(self, serialConnection):#, fine=False):
        current_duty_cycle = self.duty_cycle
        duty_cycle_delta = self.duty_cycle_delta#(self.fine_duty_cycle_delta if fine else self.duty_cycle_delta)

        if (current_duty_cycle == DUTY_CYCLE_MAX):
            print("Already at max duty cycle")
        elif (current_duty_cycle + duty_cycle_delta > DUTY_CYCLE_MAX):
            self.max_duty_cycle(serialConnection)
        else:
            self.duty_cycle = current_duty_cycle + duty_cycle_delta
            self.send_to_arduino(serialConnection)

    def decrease_duty_cycle(self, serialConnection):#, fine=False):
        current_duty_cycle = self.duty_cycle
        duty_cycle_delta = self.duty_cycle_delta#(self.fine_duty_cycle_delta if fine else self.duty_cycle_delta)

        if (current_duty_cycle == DUTY_CYCLE_MIN):
            print("Already at min duty cycle")
        elif (current_duty_cycle - duty_cycle_delta < DUTY_CYCLE_MIN):
            self.min_duty_cycle(serialConnection)
        else:
            self.duty_cycle = current_duty_cycle - duty_cycle_delta
            self.send_to_arduino(serialConnection)

    def max_duty_cycle(self, serialConnection):
        if self.duty_cycle == DUTY_CYCLE_MAX:
            print("Already at max duty cycle")
            return
        self.duty_cycle = DUTY_CYCLE_MAX
        self.send_to_arduino(serialConnection)

    def min_duty_cycle(self, serialConnection):
        if self.duty_cycle == DUTY_CYCLE_MIN:
            print("Already at min duty cycle")
            return
        self.duty_cycle = DUTY_CYCLE_MIN
        self.send_to_arduino(serialConnection)
