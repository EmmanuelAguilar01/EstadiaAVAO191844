import torch
from transformers import DetrImageProcessor, DetrForObjectDetection
import supervision as sv
import os
from PIL import Image
import cv2


def obtener_imagenes(dataset_path):
    extensiones_validas = ('.jpg', '.jpeg', '.png')
    return [os.path.join(dataset_path, f) for f in os.listdir(dataset_path) if f.lower().endswith(extensiones_validas)]


def cargar_modelo_yolo(peso_path):
    return torch.hub.load('ultralytics/yolov5', 'custom', path=peso_path)


def cargar_modelo_detr(peso_path, device):
    modelo = DetrForObjectDetection.from_pretrained(peso_path)
    modelo.to(device)
    procesador = DetrImageProcessor.from_pretrained(peso_path)
    return modelo, procesador


def evaluar_yolo(modelo_yolo, imagen):
    resultados = modelo_yolo(imagen)
    # Devuelve las predicciones como un diccionario
    return resultados.pandas().xyxy[0].to_dict(orient="records")


def evaluar_detr(modelo_detr, procesador_detr, imagen):
    # Convertir la imagen a formato PIL
    imagen_pil = Image.fromarray(cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB))

    # Preprocesar y realizar inferencia
    inputs = procesador_detr(
        images=imagen_pil, return_tensors="pt").to(modelo_detr.device)
    outputs = modelo_detr(**inputs)

    # Extraer las predicciones
    logits = outputs.logits.detach().cpu().numpy()
    boxes = outputs.pred_boxes.detach().cpu().numpy()

    return {"logits": logits.tolist(), "boxes": boxes.tolist()}
