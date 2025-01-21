import os
import json
from PIL import Image

# Rutas
images_path = "C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Datasets\\Yolo1000\\test\\images"
labels_path = "C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Datasets\\Yolo1000\\test\\labels"
output_json_path = "C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Datasets\\Yolo1000\\test\\images\\_annotations.coco.json"

# Inicializar estructura COCO
coco_format = {
    "images": [],
    "annotations": [],
    "categories": []
}

# Agregar la única categoría "Garbage"
coco_format["categories"].append({
    "id": 0,  # ID único de la categoría
    "name": "Garbage",
    "supercategory": "none"
})

# Procesar imágenes y anotaciones
annotation_id = 1  # ID único para cada anotación
for img_id, img_file in enumerate(os.listdir(images_path)):
    if img_file.endswith(('.jpg', '.png')):
        # Información de la imagen
        img_path = os.path.join(images_path, img_file)
        img = Image.open(img_path)
        width, height = img.size

        coco_format["images"].append({
            "id": img_id,
            "file_name": img_file,
            "height": height,
            "width": width
        })

        # Leer archivo de anotaciones (YOLO)
        label_file = os.path.join(
            labels_path, os.path.splitext(img_file)[0] + ".txt")
        if os.path.exists(label_file):
            with open(label_file, 'r') as f:
                for line in f:
                    _, x_center, y_center, bbox_width, bbox_height = map(
                        float, line.strip().split())

                    # Convertir a formato COCO
                    x_min = (x_center - bbox_width / 2) * width
                    y_min = (y_center - bbox_height / 2) * height
                    bbox_width *= width
                    bbox_height *= height

                    coco_format["annotations"].append({
                        "id": annotation_id,
                        "image_id": img_id,
                        "category_id": 0,  # Siempre es "Garbage"
                        "bbox": [x_min, y_min, bbox_width, bbox_height],
                        "area": bbox_width * bbox_height,
                        "segmentation": [],
                        "iscrowd": 0
                    })
                    annotation_id += 1

# Guardar en un archivo JSON
with open(output_json_path, 'w') as json_file:
    json.dump(coco_format, json_file, indent=4)

print(f"Archivo annotations.json generado en {output_json_path}")
