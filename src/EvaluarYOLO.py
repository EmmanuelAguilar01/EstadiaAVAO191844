import subprocess
import argparse
import os
import sys


def ejecutar_detect(weights, img_size, conf_thres, iou_thres, source, guardado):
    """
    Ejecuta el archivo detect.py con los hiperparámetros.

    Argumentos:
        weights (str): Ruta al archivo .pt con los pesos entrenados.
        img_size (int): Tamaño de la imagen para la inferencia.
        conf_thres (float): Umbral de confianza para las detecciones.
        iou_thres (float): Umbral de IoU (Intersection over Union).
        source (str): Ruta al directorio o archivo de entrada.
    """
    directorio_script = os.path.dirname(os.path.abspath(__file__))
    directorio_base = os.path.dirname(directorio_script)
    ruta_python = sys.executable
    ruta_detect = os.path.join(
        directorio_base, "src", "Models", "YoloV5", "detect.py")

    try:
        # Construir el comando
        comando = [
            ruta_python,
            ruta_detect,
            "--weights", weights,
            "--img", str(img_size),
            "--conf-thres", str(conf_thres),
            "--iou-thres", str(iou_thres),
            "--source", source,
            "--project", guardado
        ]

        # Ejecutar el comando
        resultado = subprocess.run(comando, capture_output=True, text=True)

        # Verificar si hubo errores
        if resultado.returncode == 0:
            print("Ejecución exitosa:")
            print(resultado.stdout)
        else:
            print("Error en la ejecución:")
            print(resultado.stderr)

    except Exception as e:
        print(f"Error al ejecutar detect.py: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ejecutar detect.py con YOLOv5")
    parser.add_argument("--weights", required=True,
                        help="Ruta al archivo de pesos (.pt)")
    parser.add_argument("--source", required=True,
                        help="Ruta al directorio o archivo de entrada")
    parser.add_argument("--guardado", required=True,
                        help="Ruta donde se guardarán los resultados")

    args = parser.parse_args()

    # Parámetros de entrada
    weights_path = args.weights
    img_size = 416
    conf_thres = 0.35
    iou_thres = 0.4
    source_path = args.source
    guardado = args.guardado
    # Llamar a la función
    ejecutar_detect(weights_path, img_size, conf_thres,
                    iou_thres, source_path, guardado)
