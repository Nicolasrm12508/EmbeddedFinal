import os
import threading
from flask import Flask, request, send_from_directory, render_template_string, make_response

app = Flask(__name__)

# --- Configuración ---
IMAGE_DIR = r"C:\Users\nicol\Downloads\ov7670\imagenes"
os.makedirs(IMAGE_DIR, exist_ok=True)

# --- Variables globales ---
last_image_name = None
image_counter = 1
lock = threading.Lock()

# --- Conversión RGB565 → RGB888 ---
def rgb565_to_rgb888(rgb565_bytes):
    result = bytearray()
    for i in range(0, len(rgb565_bytes), 2):
        pixel = (rgb565_bytes[i] << 8) | rgb565_bytes[i + 1]
        r = (pixel >> 11) & 0x1F
        g = (pixel >> 5) & 0x3F
        b = pixel & 0x1F
        r = (r << 3) | (r >> 2)
        g = (g << 2) | (g >> 4)
        b = (b << 3) | (b >> 2)
        result.extend([b, g, r])
    return bytes(result)

# --- Guardado BMP correctamente orientado y sin reflejo horizontal ---
def save_bmp(width, height, rgb888_data, filename):
    row_size = (width * 3 + 3) & ~3
    padding = row_size - width * 3
    bmp_data = bytearray()
    for row in range(0, height):
        start = row * width * 3
        row_data = rgb888_data[start:start + width * 3]
        flipped_row = bytearray()
        for col in range(width):
            pixel_start = (width - 1 - col) * 3
            flipped_row.extend(row_data[pixel_start:pixel_start + 3])
        bmp_data.extend(flipped_row)
        bmp_data.extend(b'\x00' * padding)
    file_size = 54 + len(bmp_data)
    bmp_header = bytearray([
        0x42, 0x4D,
        *file_size.to_bytes(4, 'little'), 0x00, 0x00, 0x00, 0x00, 0x36, 0x00, 0x00, 0x00,
        0x28, 0x00, 0x00, 0x00,
        *width.to_bytes(4, 'little'),
        *height.to_bytes(4, 'little'),
        0x01, 0x00, 0x18, 0x00,
        0x00, 0x00, 0x00, 0x00,
        *len(bmp_data).to_bytes(4, 'little'),
        0x13, 0x0B, 0x00, 0x00, 0x13, 0x0B, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    ])
    with open(filename, "wb") as f:
        f.write(bmp_header)
        f.write(bmp_data)

# --- CORS ---
@app.after_request
def apply_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Connection"] = "close"
    return response

@app.route("/")
def home():
    return "<h2>Servidor listo para recibir imágenes</h2><a href='/view'>Ver imagen</a>"

# --- Subida de imagen desde la Pico W ---
@app.route("/upload_raw_image_flash/", methods=["POST"])
def upload_image():
    global last_image_name, image_counter
    data = request.get_data()
    if len(data) < 4:
        return "", 400

    width = int.from_bytes(data[0:2], 'big')
    height = int.from_bytes(data[2:4], 'big')
    image_data = data[4:]

    if len(image_data) != width * height * 2:
        return "", 400

    rgb888_data = rgb565_to_rgb888(image_data)

    with lock:
        filename = f"{image_counter:04d}.bmp"
        filepath = os.path.join(IMAGE_DIR, filename)
        save_bmp(width, height, rgb888_data, filepath)
        last_image_name = filename
        image_counter += 1

    return "", 200

@app.route("/last_image_name")
def last_image_name_route():
    with lock:
        return {"image_name": last_image_name} if last_image_name else {}

@app.route("/images/<path:filename>")
def serve_image(filename):
    response = make_response(send_from_directory(IMAGE_DIR, filename))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/view")
def view_canvas():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vista en Tiempo Real</title>
        <style>
            body {
                background-color: #000;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            canvas {
                border: 2px solid #444;
            }
        </style>
    </head>
    <body>
        <canvas id="liveCanvas" width="320" height="240"></canvas>
        <script>
            let currentImage = null;
            const canvas = document.getElementById("liveCanvas");
            const ctx = canvas.getContext("2d");
            const img = new Image();

            async function fetchLatestImageName() {
                try {
                    const res = await fetch("/last_image_name");
                    const data = await res.json();
                    return data.image_name;
                } catch (err) {
                    console.error("Error al obtener nombre de imagen:", err);
                    return null;
                }
            }

            async function updateCanvas() {
                const imageName = await fetchLatestImageName();
                if (imageName && imageName !== currentImage) {
                    img.src = `/images/${imageName}?t=${Date.now()}`;
                    img.onload = () => {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        currentImage = imageName;
                    };
                }
                requestAnimationFrame(updateCanvas);
            }

            requestAnimationFrame(updateCanvas);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
