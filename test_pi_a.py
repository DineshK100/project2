import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)

def read_adc(channel):
    command = [1, (8 + channel) << 4, 0]
    response = spi.xfer2(command)
    value = ((response[1] & 3) << 8) + response[2]
    return value

while True:
    ldr = read_adc(0)
    pot = read_adc(1)
    print(f"LDR: {ldr:4d}, POT: {pot:4d}")
    time.sleep(0.5)
