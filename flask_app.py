from flask import Flask

app = Flask(__name__)

@app.route("/")
def inicio():
    pagina = """
    <!DOCTYPE html>
    <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Python Web Lab</title>
        </head>
        <body>
            <h1>Mi primera aplicación web con Python</h1>
            <p>Servidor Python funcionando correctamente.</p>
            <p>Laboratorio de despliegue web.</p>
            <p>Versión 2 - Actualizado desde GitHub.</p>
        </body>
    </html>
    """

    return pagina
