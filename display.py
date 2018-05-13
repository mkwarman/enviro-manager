import RPi_I2C_driver

spinner_chars = [
        # Char 0 - "-"
        [ 0x00, 0x00, 0x00, 0x00, 0x1f, 0x00, 0x00, 0x00 ],
        # Char 1 - "\"
        [ 0x10, 0x08, 0x08, 0x04, 0x04, 0x02, 0x02, 0x01 ],
        # Char 2 - "|"
        [ 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04 ],
        # Char 3 - "/"
        [ 0x00, 0x10, 0x08, 0x04, 0x02, 0x01, 0x00, 0x00 ],
]

class Display:
    display = None
    current_spinner_char = 0

    def __init__(self):
        self.display = RPi_I2C_driver.lcd()
        self.update("Loading,", 1)
        self.update("Please wait...", 2)

        self.display.lcd_load_custom_chars(spinner_chars)

    def update(self, text, line):
        # Update the spinner
        if self.current_spinner_char >= len(spinner_chars):
            self.current_spinner_char = 0
        self.display.lcd_display_string("Data:", 1)
        self.display.lcd_display_string_pos(chr(self.current_spinner_char), 1, 19)
        self.current_spinner_char += 1
        
        self.display.lcd_display_string(text, line)

    def off(self):
        self.display.lcd_clear()
        self.display.backlight(0)

