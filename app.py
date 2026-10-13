from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class MiServidor(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        pagina = """
        <html>
            <head>
                <title>Python Web Lab</title>
            </head>
            <body>
                <h1>Mi primera aplicación web con Python</h1>
                <p>Servidor Python funcionando correctamente.</p>
                <p>Laboratorio de despliegue web.</p>
            </body>
        </html>
        """

        self.wfile.write(pagina.encode("utf-8"))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))

    servidor = HTTPServer(("0.0.0.0", puerto), MiServidor)

    print(f"Servidor iniciado en el puerto {puerto}", flush=True)

    servidor.serve_forever()
