
from http.server import HTTPServer, BaseHTTPRequestHandler

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
    servidor = HTTPServer(("127.0.0.1", 8080), MiServidor)
    print("Servidor iniciado en http://127.0.0.1:8080")
    servidor.serve_forever()
