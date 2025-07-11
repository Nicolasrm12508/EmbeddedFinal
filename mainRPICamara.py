import machine
import time
import sys
import gc
import network
import urequests as requests
from machine import Pin, I2C, PWM
from ov7670_wrapper import *  # Asegúrate de tener esta librería

# --- Configuración de red Wi-Fi ---
SSID = "CentralAPT"
PASSWORD = "12345678"
IP_ESTATICA = "192.168.0.40"
MASCARA_SUBRED = "255.255.255.0"
PUERTA_ENLACE = "192.168.0.254"
DNS_PRIMARIO = "8.8.8.8"
DNS_SECUNDARIO = "8.8.4.4"

# --- Dirección del servidor Flask ---
FLASH_SERVER_URL = "http://192.168.0.100:8000"
UPLOAD_ENDPOINT = "/upload_raw_image_flash/"
DEVICE_IP = IP_ESTATICA

# --- Secuencia de imágenes ---
image_sequence_number = 0

# --- Conexión a Wi-Fi con IP estática ---
def conectar_wifi_estatico(ssid, password, ip_estatica, mascara_subred, puerta_enlace, dns_primario, dns_secundario=None):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a la red Wi-Fi con IP estática...")
        wlan.ifconfig((ip_estatica, mascara_subred, puerta_enlace, dns_primario))
        wlan.connect(ssid, password)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("\n✅ Conectado a Wi-Fi")
        print(f"IP: {wlan.ifconfig()[0]}")
        return True
    else:
        print("\n❌ No se pudo conectar a Wi-Fi")
        return False

# --- Configura MCLK para la cámara ---
print("🔧 Configurando MCLK...")
pwm = PWM(Pin(22))
pwm.freq(30_000_000)
pwm.duty_u16(32768)

# --- Inicializa I2C y la cámara ---
print("🔧 Inicializando I2C y OV7670...")
i2c = I2C(0, freq=400_000, scl=Pin(13), sda=Pin(12))

try:
    ov7670 = OV7670Wrapper(
        i2c_bus=i2c,
        mclk_pin_no=22,
        pclk_pin_no=21,
        data_pin_base=2,
        vsync_pin_no=17,
        href_pin_no=26,
        reset_pin_no=14,
        shutdown_pin_no=15,
    )
    ov7670.wrapper_configure_rgb()
    ov7670.wrapper_configure_base()
    width, height = ov7670.wrapper_configure_size(OV7670_WRAPPER_SIZE_DIV4)
    i2c.writeto_mem(0x21, 0x13, b'\xE7')  # Activar auto gain/exposure
    ov7670.wrapper_configure_test_pattern(OV7670_WRAPPER_TEST_PATTERN_NONE)

    print(f"📷 Cámara lista. Resolución: {width}x{height}")
    frame_buf = bytearray(width * height * 2)
    gc.collect()
except Exception as e:
    print(f"❌ Error inicializando la cámara: {e}")
    sys.exit(1)

# --- Conectar a red ---
if not conectar_wifi_estatico(SSID, PASSWORD, IP_ESTATICA, MASCARA_SUBRED, PUERTA_ENLACE, DNS_PRIMARIO, DNS_SECUNDARIO):
    sys.exit()

# --- Enviar imagen al servidor (sin esperar respuesta) ---
def send_image_to_flash(image_data_buffer, img_width, img_height, seq_num):
    try:
        full_raw_image_data = img_width.to_bytes(2, 'big') + \
                              img_height.to_bytes(2, 'big') + \
                              image_data_buffer
        headers = {
            "Content-Type": "application/octet-stream",
            "X-Device-IP": DEVICE_IP,
            "X-Image-Sequence": str(seq_num)
        }
        requests.post(f"{FLASH_SERVER_URL}{UPLOAD_ENDPOINT}", data=full_raw_image_data, headers=headers)
        print(f"📤 Imagen enviada. Secuencia: {seq_num}")
    except Exception as e:
        print(f"❌ Error al enviar imagen (seq {seq_num}): {e}")

# --- Bucle principal de captura ---
if __name__ == "__main__":
    gc.collect()
    while True:
        print("\n--- Capturando imagen ---")
        ov7670.capture(frame_buf)
        print("✅ Imagen capturada")

        image_sequence_number += 1
        print(f"🧮 Número de secuencia: {image_sequence_number}")

        send_image_to_flash(frame_buf, width, height, image_sequence_number)

        time.sleep(0.5)

