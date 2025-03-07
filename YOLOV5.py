import os
import time
import csv
import json
import glob
import shutil
import warnings
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import yaml
import pandas as pd
import train
import detect
from train import parse_opt as parse_opt_train
from detect import parse_opt as parse_opt_detect
import argparse

warnings.filterwarnings(
    "ignore", message="The name tf.losses.sparse_softmax_cross_entropy * ", category=FutureWarning)

warnings.filterwarnings("ignore", category=DeprecationWarning)


class Dataset:
    def __init__(self, location):
        self.location = location


def procesar_metricas(archivo_CSV, direccionJson, Tiempo_Formato, nombre, directorioPersonalizado):
    mejor_map = -1  # Para encontrar el mejor mAP
    mejor_precision = -1

    with open(archivo_CSV, mode='r') as archivo:
        lector_csv = csv.reader(archivo)
        encabezados = next(lector_csv)  # Leer la fila de encabezados

        # Índices de las columnas de interés
        map_idx = encabezados.index("     metrics/mAP_0.5")
        precision_idx = encabezados.index("   metrics/precision")

        for fila in lector_csv:
            if len(fila) > 0:
                try:
                    # Convertir valores a float
                    map_actual = float(fila[map_idx])
                    precision_actual = float(fila[precision_idx])

                    # Verificar si el mAP actual es el mejor
                    if map_actual > mejor_map:
                        mejor_map = map_actual
                        mejor_precision = precision_actual

                except ValueError:
                    # Manejo de excepciones si alguna fila tiene un valor no numérico
                    print(f"Valor inválido en fila: {fila}")

    # Invertir el valor de mAP para calcular el porcentaje de error
    porcentaje_error = (1 - mejor_map) * 100
    mejor_precision_porcentaje = mejor_precision * 100

    ruta_completa = os.path.join(
        directorioPersonalizado, nombre, "weights", "best.pt")

    # Guardar métricas en un archivo JSON
    metricas = {
        "tiempo_formateado": Tiempo_Formato,
        "ap_50": mejor_precision_porcentaje,
        "error_50": porcentaje_error,
        "direccion": ruta_completa
    }

    with open(direccionJson, 'w') as json_file:
        json.dump(metricas, json_file, indent=4)

    print(f"Métricas guardadas")


if __name__ == '__main__':
    # Define los argumentos que se pueden pasar al script
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, required=True)
    parser.add_argument('--batch-size', type=int, required=True)
    parser.add_argument('--imgsz', type=int, required=True)
    parser.add_argument('--name', type=str, required=True)

    args = parser.parse_args()

    ruta = os.getenv('RUTA')

    dataset = Dataset(ruta)
    directorio_script = os.path.dirname(os.path.abspath(__file__))
    directorioBase = os.path.join(directorio_script,"..","..","..","src", "Pesos", "YOLO")

    data = os.path.join(ruta, "data.yaml")
    cfg = os.path.join(ruta, "custom_data.yaml")

    directorioPersonalizado = os.path.join(directorioBase, args.name)
    os.makedirs(directorioPersonalizado, exist_ok=True)

    # Leer los valores de las variables de entorno
    conf_thres = os.getenv('CONF_THRES')
    iou_thres = os.getenv('IOU_THRES')

    # Si no están definidas, usar valores por defecto
    conf_thres = float(conf_thres) if conf_thres else 0.25
    iou_thres = float(iou_thres) if iou_thres else 0.45

    with open(data, "r") as file:
        print(file.read())

    directorio_script = os.path.dirname(os.path.abspath(__file__))
    ruta_origen = os.path.join(
        directorio_script, "yolov5s.yaml")

    shutil.copyfile(ruta_origen, cfg)

    with open(cfg, "r") as file:
        print(file.read())

    # Cargar el archivo data.yaml
    with open(data, 'r') as file:
        data_config = yaml.safe_load(file)

    # Actualizar las rutas para que sean absolutas
    data_config['train'] = f"{dataset.location}/train/images"
    data_config['val'] = f"{dataset.location}/valid/images"

    # Guardar las rutas actualizadas en data.yaml
    with open(data, 'w') as file:
        yaml.safe_dump(data_config, file)

    opt_train = parse_opt_train()

    opt_train.imgsz = args.imgsz
    opt_train.batch_size = args.batch_size
    opt_train.epochs = args.epochs
    opt_train.data = data
    opt_train.cfg = cfg
    opt_train.name = args.name
    opt_train.project = directorioPersonalizado
    opt_train.cache = True

    iniciar_tiempo = time.time()

    train.main(opt_train)

    terminar_tiempo = time.time()

    Tiempo_Total = terminar_tiempo - iniciar_tiempo

    # Convertir el tiempo a horas, minutos y segundos
    hours, remainder = divmod(Tiempo_Total, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Formato de tiempo HH:MM:SS
    Tiempo_Formato = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    direccionJson = os.path.join(directorioPersonalizado, "metricas.json")
    archivo_CSV = os.path.join(
        directorioPersonalizado, args.name, "results.csv")
    nombre = args.name

    os.makedirs(os.path.dirname(direccionJson), exist_ok=True)

    with open(direccionJson, 'w') as json_file:
        json_file.write('{}')

    if os.path.exists(archivo_CSV):
        procesar_metricas(archivo_CSV, direccionJson,
                          Tiempo_Formato, nombre, directorioPersonalizado)
    else:
        print(f"El archivo {archivo_CSV} no se generó correctamente.")
