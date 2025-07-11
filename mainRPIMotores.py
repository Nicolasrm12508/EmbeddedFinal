from carro_wifi_module import CarroWiFi
import time
from EjemplosServo import BrazoRobot
from motor_controller import MotorController

# ====================
# CONFIGURACIÓN WIFI
# ====================
SSID = 'CentralAPT'
PASSWORD = '12345678'
GATEWAY = '192.168.0.254'
PUERTO_REMOTO = 1234
PUERTO_LOCAL = 1234
IP_FIJA = '192.168.0.50'

UART_TX = 0
UART_RX = 1

# ====================
# INICIALIZACIÓN
# ====================
carro = CarroWiFi(SSID, PASSWORD, GATEWAY, PUERTO_REMOTO, PUERTO_LOCAL, IP_FIJA, UART_TX, UART_RX)
controlador_rover = MotorController()
brazo = BrazoRobot()

print("🔄 Esperando mensajes UDP...")
brazo.mover_servo3(95)

# ====================
# BUCLE PRINCIPAL
# ====================
while True:
    
    mensaje = carro.recibir_del_central()

    if mensaje:
        comando = mensaje.strip().upper()
        print(f"📨 Comando recibido: {comando}")

        # Adelante
        if comando == 'FWD_S':
            print("➡ Adelante Suave")
            controlador_rover.mover_adelante(5)  # velocidad suave
        elif comando == 'FWD_R':
            print("➡ Adelante Rápido")
            controlador_rover.mover_adelante(70)  # velocidad rápida

        # Atrás
        elif comando == 'BACK_S':
            print("⬅ Atrás Suave")
            controlador_rover.mover_atras(5)
        elif comando == 'BACK_R':
            print("⬅ Atrás Rápido")
            controlador_rover.mover_atras(70)

        # Izquierda
        elif comando == 'LEFT_S':
            print("↙ Izquierda Suave")
            controlador_rover.girar_izquierda(15)
        elif comando == 'LEFT_R':
            print("↙ Izquierda Rápido")
            controlador_rover.girar_izquierda(90)

        # Derecha
        elif comando == 'RIGHT_S':
            print("↘ Derecha Suave")
            controlador_rover.girar_derecha(15)
        elif comando == 'RIGHT_R':
            print("↘ Derecha Rápido")
            controlador_rover.girar_derecha(90)

        # Recoger y soltar
        elif comando == 'GRAB':
            print("🤖 Recoger")
            brazo.recoger()
        elif comando == 'RELEASE':
            print("📤 Soltar")
            brazo.asegurar()

        else:
            print("❓ Comando no reconocido:", comando)

    time.sleep(0.1)

