import os
import socket
from flask import Flask, send_file, Response, request

# ============================
# CONFIGURACIÓN GENERAL
# ============================

CARPETA_IMAGENES = r'C:\Users\nicol\Downloads\ov7670\imagenes'  # Cambia esta ruta si es necesario
INTERVALO_ACTUALIZACION = 0.5  # en segundos

# Configuración de red (UDP)
IP_DESTINO = '192.168.0.50'  # IP de la Raspberry Pi Pico W
PUERTO_UDP = 1234

# Diccionario de comandos UDP
COMANDOS_UDP = {
    'adelante_suave': b'FWD_S',
    'adelante_rapido': b'FWD_R',
    'atras_suave': b'BACK_S',
    'atras_rapido': b'BACK_R',
    'izquierda_suave': b'LEFT_S',
    'izquierda_rapido': b'LEFT_R',
    'derecha_suave': b'RIGHT_S',
    'derecha_rapido': b'RIGHT_R',
    'recoger': b'GRAB',
    'soltar': b'RELEASE'
}

# ============================
# FLASK APP
# ============================

app = Flask(__name__)

@app.route('/')
def pagina_principal():
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Control de carrito</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: #f0f0f0;
            }}
            h1 {{
                margin-top: 20px;
            }}
            img {{
                max-width: 90%;
                margin-top: 20px;
                border: 4px solid #444;
            }}
            .control-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                max-width: 400px;
                margin: 30px auto;
            }}
            button {{
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                transition: 0.3s;
            }}
            .suave {{ background-color: #AEDFF7; }}
            .rapido {{ background-color: #4FC3F7; color: white; }}
            .accion {{ background-color: #FFC107; }}
            .accion:hover, .suave:hover, .rapido:hover {{
                transform: scale(1.05);
            }}
        </style>
    </head>
    <body>
        <h1>Control del Carrito</h1>
        <img id="imagen" src="/ultima?nocache=0"><br>

        <div class="control-grid">
            <div></div>
            <button class="suave" onclick="enviarComando('adelante_suave')">Adelante Suave</button>
            <button class="rapido" onclick="enviarComando('adelante_rapido')">Adelante Rápido</button>

            <button class="suave" onclick="enviarComando('izquierda_suave')">Izquierda Suave</button>
            <div></div>
            <button class="suave" onclick="enviarComando('derecha_suave')">Derecha Suave</button>

            <button class="rapido" onclick="enviarComando('izquierda_rapido')">Izquierda Rápido</button>
            <div></div>
            <button class="rapido" onclick="enviarComando('derecha_rapido')">Derecha Rápido</button>

            <div></div>
            <button class="suave" onclick="enviarComando('atras_suave')">Atrás Suave</button>
            <button class="rapido" onclick="enviarComando('atras_rapido')">Atrás Rápido</button>

            <button class="accion" onclick="enviarComando('recoger')">🤖 Recoger</button>
            <div></div>
            <button class="accion" onclick="enviarComando('soltar')">📤 Soltar</button>
        </div>

        <script>
            setInterval(() => {{
                const img = document.getElementById("imagen");
                img.src = "/ultima?nocache=" + new Date().getTime();
            }}, {int(INTERVALO_ACTUALIZACION * 1000)});

            function enviarComando(comando) {{
                fetch('/comando/' + comando)
                    .then(response => response.text())
                    .then(data => console.log(data))
                    .catch(err => console.error('Error al enviar comando:', err));
            }}
        </script>
    </body>
    </html>
    '''

@app.route('/ultima')
def ultima_imagen():
    try:
        archivos = sorted([
            f for f in os.listdir(CARPETA_IMAGENES)
            if f.lower().endswith(('.bmp', '.jpg', '.jpeg', '.png'))
        ])
        if not archivos:
            return Response('No hay imágenes', status=404)

        archivo_mas_reciente = archivos[-1]
        ruta_imagen = os.path.join(CARPETA_IMAGENES, archivo_mas_reciente)
        return send_file(ruta_imagen, mimetype='image/bmp')  # Asumiendo imágenes .bmp
    except Exception as e:
        return Response(f'Error: {str(e)}', status=500)

@app.route('/comando/<accion>')
def enviar_udp(accion):
    comando = COMANDOS_UDP.get(accion)
    if not comando:
        return f'Comando "{accion}" no reconocido', 400

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(comando, (IP_DESTINO, PUERTO_UDP))
        print(f"📡 Comando enviado: {accion} -> {comando}")
        return f'Comando "{accion}" enviado'
    except Exception as e:
        return f'Error enviando comando: {str(e)}', 500

# ============================
# EJECUCIÓN
# ============================

def main():
    if not os.path.exists(CARPETA_IMAGENES):
        os.makedirs(CARPETA_IMAGENES)
        print(f"📁 Carpeta creada: {CARPETA_IMAGENES}")
    else:
        print(f"📁 Carpeta existente: {CARPETA_IMAGENES}")

    print("🚀 Servidor iniciado en http://localhost:5000")
    app.run(debug=False, port=5000, use_reloader=False)

if __name__ == '__main__':
    main()