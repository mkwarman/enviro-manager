import RPi_I2C_driver

class Display:
    display = None
    display_status_indicators = ["-", "\\", "|", "/"]
    display_status_current_indicator = 0

    def __init__(self):
        self.display = RPi_I2C_driver.lcd()
        self.update("Loading,", 1)
        self.update("Please wait...", 2)

    def update(self, text, line):
        # Update the status indicator
        if self.display_status_current_indicator >= len(self.display_status_indicators):
            self.display_status_current_indicator = 0
        header = "Data:              " + self.display_status_indicators[self.display_status_current_indicator]
        self.display.lcd_display_string(header, 1)

        self.display.lcd_display_string(text, line)

        self.display_status_current_indicator += 1

    def off(self):
        self.display.lcd_clear()
        self.display.backlight(0)

