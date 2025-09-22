import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)

def read_adc(channel):
    command = [1, (8 + channel) << 4, 0]
    response = spi.xfer2(command)
    return ((response[1] & 3) << 8) + response[2]

print("=== CALIBRATION MODE ===")
print("Find your actual sensor ranges")
print()

ldr_values = []
pot_values = []

try:
    for i in range(100):  # Take 100 readings
        ldr = read_adc(0)
        pot = read_adc(1)
        
        ldr_values.append(ldr)
        pot_values.append(pot)
        
        print(f"LDR: {ldr:4d}, POT: {pot:4d} - Cover LDR and turn pot during this test")
        time.sleep(0.2)
        
except KeyboardInterrupt:
    print(f"\nActual ranges found:")
    print(f"LDR_MIN = {min(ldr_values)}")
    print(f"LDR_MAX = {max(ldr_values)}")
    print(f"POT_MIN = {min(pot_values)}")
    print(f"POT_MAX = {max(pot_values)}")