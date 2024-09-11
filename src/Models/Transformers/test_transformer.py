import time
import os
import torch
from transformers import DetrConfig, AutoModelForObjectDetection
import torchvision.transforms as transforms
import json
import PIL
from PIL import Image
from pycocotools.coco import COCO

# Cargar las anotaciones
coco = COCO(r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Datasets\hackathone.v2i.coco\test\annotations.json')

# Obtener las anotaciones para una imagen específica
image_id = 0
annotations = coco.loadAnns(coco.getAnnIds(image_id))

# Imprimir las anotaciones
for annotation in annotations:
    print(annotation)


class Pesos:
    def __init__(self):
        self.json = r"C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Pesos\Transformers\config.json"
        self.bin = r"C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Pesos\Transformers\pytorch_model.bin"


# Cargar el archivo annotations.json
with open(r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Datasets\hackathone.v2i.coco\test\annotations.json') as f:
    annotations = json.load(f)

category_to_label = {category['id']: category['name']
                     for category in annotations['categories']}
label_to_category = {v: k for k, v in category_to_label.items()}

# Directorio de las imágenes de prueba
test_dir = r'C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Datasets\hackathone.v2i.coco\test'

# Inicializar las métricas
total_loss = 0
total_correct = 0
total_images = 0
total_true_positives = 0
total_false_positives = 0
total_false_negatives = 0

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

pesos = Pesos()

# Cargar la configuración del modelo
config = DetrConfig.from_pretrained(pesos.json)

# Crear un nuevo modelo de transformers con la misma arquitectura
model = AutoModelForObjectDetection.from_pretrained(pesos.bin, config=config)

print(model.config)
print(model.config.id2label)

# Evaluar el modelo
model.eval()

if __name__ == '__main__':
    start_time = time.time()

    # Filtrar solo archivos de imagen
    valid_image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

    for filename in os.listdir(test_dir):
        if not any(filename.lower().endswith(ext) for ext in valid_image_extensions):
            continue

        image_path = os.path.join(test_dir, filename)

        try:
            image = PIL.Image.open(image_path)
            image_tensor = transform(image).unsqueeze(0)
        except PIL.UnidentifiedImageError:
            print(f"Archivo no identificable como imagen: {filename}")
            continue

        # Obtener el id de la imagen desde el nombre del archivo
        image_info = next(
            (img for img in annotations['images'] if img['file_name'] == filename), None)
        if image_info is None:
            print(f"Información de imagen no encontrada para {filename}")
            continue

        image_id = image_info['id']

        # Buscar la anotación correspondiente usando el 'image_id'
        annotations_for_image = [
            ann for ann in annotations['annotations'] if ann['image_id'] == image_id]
        if not annotations_for_image:
            print(f"Anotaciones no encontradas para {filename}")
            continue

        # Asumimos que solo hay una anotación por imagen
        annotation = annotations_for_image[0]
        true_label = torch.tensor([annotation['category_id']])

        # Pasar la imagen a través del modelo
        with torch.no_grad():
            outputs = model(image_tensor)
            logits = outputs.logits

        # Obtener la predicción más probable para cada objeto detectado
        num_queries = logits.shape[1]  # Número de consultas del modelo
        # Obtener la clase más probable por consulta
        predicted_labels = logits.argmax(dim=-1)

        # Aquí usamos la clase más probable de la primera consulta para evaluación
        # Solo la primera consulta
        predicted_label = predicted_labels[0][0].item()

        # Calcular la pérdida para la primera predicción
        loss = torch.nn.functional.cross_entropy(
            logits[0, 0, :].unsqueeze(0), true_label)

        # Acumular la pérdida
        total_loss += loss.item()

        # Evaluar la predicción más probable con la etiqueta verdadera
        if predicted_label == true_label.item():
            total_correct += 1
            total_true_positives += 1
        else:
            total_false_negatives += 1
            total_false_positives += 1

        total_images += 1

    avg_loss = total_loss / total_images
    accuracy = total_correct / total_images
    recall = total_true_positives / \
        (total_true_positives + total_false_negatives)
    specificity = total_true_positives / \
        (total_true_positives + total_false_positives)

    # Imprimir las métricas finales
    print("Pérdida promedio:", avg_loss)
    print("Precisión promedio:", accuracy)
    print("Sensibilidad promedio:", recall)
    print("Especificidad promedio:", specificity)

    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    print(f"Tiempo total de evaluación: {elapsed_time} segundos")
