import csv


def procesar_metricas(archivo_csv, archivo_salida):
    mejor_map = -1  # Para encontrar el mejor mAP
    mejor_precision = -1
    tiempo = ""

    with open(archivo_csv, mode='r') as archivo:
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

                    # Guardar el tiempo de la última fila
                    tiempo = fila[-1]

                except ValueError:
                    # Manejo de excepciones si alguna fila tiene un valor no numérico
                    print(f"Valor inválido en fila: {fila}")

    # Invertir el valor de mAP para calcular el porcentaje de error
    porcentaje_error = (1 - mejor_map) * 100
    mejor_precision_porcentaje = mejor_precision * 100
    mejor_map_porcentaje = mejor_map * 100

    # Escribir las métricas en un archivo de texto
    with open(archivo_salida, mode='w') as archivo_salida_txt:
        archivo_salida_txt.write(
            f"Mejor Precisión: {mejor_precision_porcentaje:.2f}%\n")
        archivo_salida_txt.write(
            f"Porcentaje de error (basado en mAP): {porcentaje_error:.2f}%\n")
        archivo_salida_txt.write(f"Tiempo final de ejecución: {tiempo}\n")

    print(f"Métricas guardadas en {archivo_salida}")


# Uso del código
archivo_csv = 'C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Pesos\\YOLO\\30\\train\\yolov5s_results\\results.csv'
archivo_salida = 'C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Pesos\\YOLO\\30\\train\\yolov5s_results\\Metricas.txt'

procesar_metricas(archivo_csv, archivo_salida)

########################################## DETECTOR YOLO####################################################
"""    opt_detect = parse_opt_detect()

    opt_detect.weights = r"C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Pesos\YOLO\yolov5s_results\weights\best.pt"
    opt_detect.imgsz = (args.imgsz, args.imgsz)
    opt_detect.conf_thres = conf_thres
    opt_detect.iou_thres = iou_thres
    opt_detect.source = f"{dataset.location}/test/images"
    opt_detect.name = r"C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Pesos\YOLO\yolov5s_results\test"

    detect.main(opt_detect)

    for imageName in glob.glob(r"C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Pesos\YOLO\yolov5s_results\test\*.jpg"):
        img = mpimg.imread(imageName)  # Lee la imagen con matplotlib
        plt.imshow(img)  # Muestra la imagen
        plt.show()  # Muestra la imagen en una ventana
"""
