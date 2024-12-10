import os
import torch
import json
import argparse
from transformers import DetrImageProcessor, DetrForObjectDetection
from pytorch_lightning import LightningModule
from torchvision.transforms import functional as F
from PIL import Image, ImageDraw
from tqdm import tqdm


class CustomDetrModel(LightningModule):
    def __init__(self):
        super().__init__()
        self.model = DetrForObjectDetection.from_pretrained(
            "facebook/detr-resnet-50", num_labels=2, ignore_mismatched_sizes=True
        ).to(device)

    def forward(self, *args, **kwargs):
        return self.model(*args, **kwargs)


def evaluar_modelo(ckpt_path, dataset_coco_path, output_dir, device="cuda"):
    """
    Evalúa un modelo DETR desde un checkpoint de PyTorch Lightning.

    Args:
        ckpt_path (str): Ruta al archivo .ckpt.
        dataset_coco_path (str): Ruta al archivo .json del dataset en formato COCO.
        output_dir (str): Directorio para guardar las imágenes con detecciones.
        device (str): Dispositivo ('cuda' o 'cpu').
    """

    # Cargar modelo desde checkpoint
    model = CustomDetrModel.load_from_checkpoint(
        ckpt_path, num_classes=2
    ).to(device)
    model.eval()

    # Procesador para imágenes
    image_processor = DetrImageProcessor.from_pretrained(
        "facebook/detr-resnet-50")

    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)

    # Procesar dataset
    with open(dataset_coco_path, "r") as f:
        dataset = json.load(f)
    images = dataset["images"]

    for img_info in tqdm(images, desc="Procesando imágenes"):
        img_path = os.path.join(os.path.dirname(
            dataset_coco_path), img_info["file_name"])
        image = Image.open(img_path).convert("RGB")
        inputs = image_processor(images=image, return_tensors="pt").to(device)

        # Inferencia
        outputs = model(**inputs)

        # Obtener logits y calcular etiquetas predichas
        logits = outputs["logits"]  # Puntuaciones sin procesar para cada clase
        pred_labels = torch.argmax(logits, dim=-1)  # Etiquetas predichas

        # Extraer pred_boxes y scores
        pred_boxes = outputs["pred_boxes"]
        scores = logits.softmax(-1).max(-1).values  # Puntajes de confianza

       # Diccionario para almacenar la mejor predicción por etiqueta
        best_predictions = {}

        # Iterar sobre las predicciones (cajas, etiquetas y puntuaciones)
        for i, (box, label, score) in enumerate(zip(pred_boxes, pred_labels, scores)):
            for j in range(score.size(0)):
                individual_score = score[j].item()
                label_id = label[j].item()

                # Excluir clase 2
                if label_id == 2:  # Ajusta este valor al ID de la clase que deseas excluir
                    continue

                if individual_score > 0.5:  # Filtrar detecciones con baja confianza
                    # Desnormalizar coordenadas de las cajas
                    width, height = image.size
                    box_coordinates = box[j].cpu().detach().numpy()

                    x_center, y_center, w, h = box_coordinates
                    x_min = (x_center - w / 2) * width
                    y_min = (y_center - h / 2) * height
                    x_max = (x_center + w / 2) * width
                    y_max = (y_center + h / 2) * height

                    # Validar y ajustar coordenadas si es necesario
                    x_min, y_min = max(0, x_min), max(0, y_min)
                    x_max, y_max = min(width, x_max), min(height, y_max)

                    # Verificar coordenadas válidas
                    if x_min < x_max and y_min < y_max:
                        if label_id not in best_predictions or best_predictions[label_id]["score"] < individual_score:
                            best_predictions[label_id] = {
                                "box": (x_min, y_min, x_max, y_max),
                                "score": individual_score,
                            }

        # Dibujar solo la mejor predicción por etiqueta
        draw = ImageDraw.Draw(image)
        for label, data in best_predictions.items():
            box = data["box"]
            score = data["score"]
            draw.rectangle(box, outline="red", width=3)
            draw.text((box[0], box[1]),
                      f"Clase {label}: {score:.2f}", fill="red")

        # Guardar imagen con anotaciones
        output_path = os.path.join(output_dir, img_info["file_name"])
        image.save(output_path)


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
    ckpt_path = args.weights  # Ruta al .ckpt
    # Ruta al archivo .json del conjunto de datos COCO
    dataset_coco_path = os.path.join(args.source, '_annotations.coco.json')
    # Directorio para guardar imágenes con detecciones
    output_dir = args.guardado
    device = "cuda" if torch.cuda.is_available() else "cpu"

    evaluar_modelo(ckpt_path, dataset_coco_path, output_dir, device)
