import os
import json
import time
from datetime import timedelta
import warnings
import random
import supervision
from transformers import DetrForObjectDetection, DetrImageProcessor
import pytorch_lightning as pl
from pytorch_lightning import Trainer
import torch
import cv2
import numpy as np
from torch.utils.data import DataLoader
from coco_eval import CocoEvaluator
import torchvision
from tqdm import tqdm
from pycocotools.coco import COCO
import argparse

warnings.filterwarnings(
    "ignore", message="`resume_download` is deprecated * ", category=FutureWarning)
warnings.filterwarnings(
    "ignore", message="The `max_size` parameter is deprecated", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# settings
DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
CHECKPOINT = 'facebook/detr-resnet-50'

image_processor = DetrImageProcessor.from_pretrained(CHECKPOINT)
model = DetrForObjectDetection.from_pretrained(CHECKPOINT)
model.to(DEVICE)


class Dataset:
    def __init__(self, location):
        self.location = location


class CocoDetection(torchvision.datasets.CocoDetection):
    def __init__(
        self,
        image_directory_path: str,
        image_processor,
        train: bool = True
    ):
        annotation_file_path = os.path.join(
            image_directory_path, ANNOTATION_FILE_NAME)
        super(CocoDetection, self).__init__(
            image_directory_path, annotation_file_path)
        self.image_processor = image_processor

    def __getitem__(self, idx):
        images, annotations = super(CocoDetection, self).__getitem__(idx)
        image_id = self.ids[idx]
        annotations = {'image_id': image_id, 'annotations': annotations}
        encoding = self.image_processor(
            images=images, annotations=annotations, return_tensors="pt")
        pixel_values = encoding["pixel_values"].squeeze()
        target = encoding["labels"][0]

        return pixel_values, target


class Detr(pl.LightningModule):

    def __init__(self, lr, lr_backbone, weight_decay):
        super().__init__()
        self.model = DetrForObjectDetection.from_pretrained(
            pretrained_model_name_or_path=CHECKPOINT,
            num_labels=len(id2label),
            ignore_mismatched_sizes=True
        )

        self.lr = lr
        self.lr_backbone = lr_backbone
        self.weight_decay = weight_decay

    def forward(self, pixel_values, pixel_mask):
        return self.model(pixel_values=pixel_values, pixel_mask=pixel_mask)

    def common_step(self, batch, batch_idx):
        pixel_values = batch["pixel_values"]
        pixel_mask = batch["pixel_mask"]
        labels = [{k: v.to(self.device) for k, v in t.items()}
                  for t in batch["labels"]]

        outputs = self.model(pixel_values=pixel_values,
                             pixel_mask=pixel_mask, labels=labels)

        loss = outputs.loss
        loss_dict = outputs.loss_dict

        return loss, loss_dict

    def training_step(self, batch, batch_idx):
        loss, loss_dict = self.common_step(batch, batch_idx)
        # logs metrics for each training_step, and the average across the epoch
        self.log("training_loss", loss)
        for k, v in loss_dict.items():
            self.log("train_" + k, v.item())

        return loss

    def validation_step(self, batch, batch_idx):
        loss, loss_dict = self.common_step(batch, batch_idx)
        self.log("validation/loss", loss)
        for k, v in loss_dict.items():
            self.log("validation_" + k, v.item())

        return loss

    def configure_optimizers(self):
        param_dicts = [
            {
                "params": [p for n, p in self.named_parameters() if "backbone" not in n and p.requires_grad]},
            {
                "params": [p for n, p in self.named_parameters() if "backbone" in n and p.requires_grad],
                "lr": self.lr_backbone,
            },
        ]
        return torch.optim.AdamW(param_dicts, lr=self.lr, weight_decay=self.weight_decay)

    def train_dataloader(self):
        return TRAIN_DATALOADER

    def val_dataloader(self):
        return VAL_DATALOADER


def collate_fn(batch):
    pixel_values = [item[0] for item in batch]
    encoding = image_processor.pad(pixel_values, return_tensors="pt")
    labels = [item[1] for item in batch]
    return {
        'pixel_values': encoding['pixel_values'],
        'pixel_mask': encoding['pixel_mask'],
        'labels': labels
    }

def convert_to_xywh(boxes):
        xmin, ymin, xmax, ymax = boxes.unbind(1)
        return torch.stack((xmin, ymin, xmax - xmin, ymax - ymin), dim=1)

def prepare_for_coco_detection(predictions):
    coco_results = []
    for original_id, prediction in predictions.items():
        if len(prediction) == 0:
            continue

        boxes = prediction["boxes"]
        boxes = convert_to_xywh(boxes).tolist()
        scores = prediction["scores"].tolist()
        labels = prediction["labels"].tolist()

        coco_results.extend(
            [
                {
                    "image_id": original_id,
                    "category_id": labels[k],
                    "bbox": box,
                    "score": scores[k],
                }
                for k, box in enumerate(boxes)
            ]
        )
    return coco_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epocas", type=int, required=True)
    parser.add_argument("--batch_size", type=int, required=True)
    parser.add_argument("--threshold", type=float, required=True)
    parser.add_argument("--iou_threshold", type=float, required=True)
    parser.add_argument("--ruta", type=str, required=True)
    parser.add_argument("--name", type=str, required=True)
    args = parser.parse_args()

    dataset = Dataset(args.ruta)

    # Define tu ruta personalizada para guardar los logs
    directorioBase = "C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Pesos\\Transformers"

    directorioPersonalizado = os.path.join(directorioBase, args.name)
    os.makedirs(directorioPersonalizado, exist_ok=True)

    ANNOTATION_FILE_NAME = "_annotations.coco.json"
    TRAIN_DIRECTORY = os.path.join(dataset.location, "train")
    VAL_DIRECTORY = os.path.join(dataset.location, "valid")
    TEST_DIRECTORY = os.path.join(dataset.location, "test")

    CONFIDENCE_TRESHOLD = args.threshold
    IOU_TRESHOLD = args.iou_threshold

    TRAIN_DATASET = CocoDetection(
        image_directory_path=TRAIN_DIRECTORY,
        image_processor=image_processor,
        train=True)
    VAL_DATASET = CocoDetection(
        image_directory_path=VAL_DIRECTORY,
        image_processor=image_processor,
        train=False)
    TEST_DATASET = CocoDetection(
        image_directory_path=TEST_DIRECTORY,
        image_processor=image_processor,
        train=False)

    print("Number of training examples:", len(TRAIN_DATASET))
    print("Number of validation examples:", len(VAL_DATASET))
    print("Number of test examples:", len(TEST_DATASET))

    # select random image
    image_ids = TRAIN_DATASET.coco.getImgIds()
    image_id = random.choice(image_ids)
    print('Image #{}'.format(image_id))

    # load image and annotatons
    image = TRAIN_DATASET.coco.loadImgs(image_id)[0]
    annotations = TRAIN_DATASET.coco.imgToAnns[image_id]
    image_path = os.path.join(TRAIN_DATASET.root, image['file_name'])
    image = cv2.imread(image_path)

    # annotate
    detections = supervision.Detections.from_coco_annotations(
        coco_annotation=annotations)

    # we will use id2label function for training
    categories = TRAIN_DATASET.coco.cats
    id2label = {k: v['name'] for k, v in categories.items()}

    labels = [
        f"{id2label[class_id]}"
        for _, _, class_id, _
        in detections
    ]

    box_annotator = supervision.BoxAnnotator()
    frame = box_annotator.annotate(
        scene=image, detections=detections, labels=labels)

    TRAIN_DATALOADER = DataLoader(
        dataset=TRAIN_DATASET, collate_fn=collate_fn, batch_size=args.batch_size, shuffle=True, num_workers=4)
    VAL_DATALOADER = DataLoader(
        dataset=VAL_DATASET, collate_fn=collate_fn, batch_size=args.batch_size)
    TEST_DATALOADER = DataLoader(
        dataset=TEST_DATASET, collate_fn=collate_fn, batch_size=args.batch_size)

    model = Detr(lr=0.0005, lr_backbone=0.0001, weight_decay=0.01)

    batch = next(iter(TRAIN_DATALOADER))
    outputs = model(pixel_values=batch['pixel_values'],
                    pixel_mask=batch['pixel_mask'])

    outputs.logits.shape

    # settings
    MAX_EPOCHS = args.epocas

    iniciar_tiempo = time.time()

    trainer = Trainer(devices=1, accelerator="cpu", max_epochs=MAX_EPOCHS,
                      gradient_clip_val=0.1, accumulate_grad_batches=8, log_every_n_steps=5, default_root_dir=directorioPersonalizado)

    trainer.fit(model)

    terminar_tiempo = time.time()

    tiempo_total = terminar_tiempo - iniciar_tiempo

    tiempo_formateado = str(timedelta(seconds=tiempo_total))

    CHECKP_DIR = "C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Checkpoints"
    CHECKPOINT_PATH = os.path.join(CHECKP_DIR, args.name)
    os.makedirs(CHECKPOINT_PATH, exist_ok=True)

    trainer.save_checkpoint(CHECKPOINT_PATH)

    model.to(DEVICE)

    # utils
    categories = TEST_DATASET.coco.cats
    id2label = {k: v['name'] for k, v in categories.items()}
    box_annotator = supervision.BoxAnnotator()

    # select random image
    image_ids = TEST_DATASET.coco.getImgIds()
    image_id = random.choice(image_ids)
    print('Image #{}'.format(image_id))

    # load image and annotatons
    image = TEST_DATASET.coco.loadImgs(image_id)[0]
    annotations = TEST_DATASET.coco.imgToAnns[image_id]
    image_path = os.path.join(TEST_DATASET.root, image['file_name'])
    image = cv2.imread(image_path)

    # annotate
    detections = supervision.Detections.from_coco_annotations(
        coco_annotation=annotations)
    labels = [f"{id2label[class_id]}" for _, _, class_id, _ in detections]
    frame = box_annotator.annotate(
        scene=image.copy(), detections=detections, labels=labels)

    print('ground truth')

    # inference
    with torch.no_grad():

        # load image and predict
        inputs = image_processor(images=image, return_tensors='pt').to(DEVICE)
        outputs = model(**inputs)

        # post-process
        target_sizes = torch.tensor([image.shape[:2]]).to(DEVICE)
        results = image_processor.post_process_object_detection(
            outputs=outputs,
            threshold=CONFIDENCE_TRESHOLD,
            target_sizes=target_sizes
        )[0]

    # annotate
    detections = supervision.Detections.from_transformers(
        transformers_results=results).with_nms(threshold=args.iou_threshold)
    labels = [f"{id2label[class_id]} {confidence:.2f}" for _,
              confidence, class_id, _ in detections]
    frame = box_annotator.annotate(
        scene=image.copy(), detections=detections, labels=labels)

    print('detections')

    evaluator = CocoEvaluator(coco_gt=TEST_DATASET.coco, iou_types=["bbox"])

    print("Running evaluation...")

    for idx, batch in enumerate(tqdm(TEST_DATALOADER)):
        pixel_values = batch["pixel_values"].to(DEVICE)
        pixel_mask = batch["pixel_mask"].to(DEVICE)
        labels = [{k: v.to(DEVICE) for k, v in t.items()}
                  for t in batch["labels"]]

        with torch.no_grad():
            outputs = model(pixel_values=pixel_values, pixel_mask=pixel_mask)

        orig_target_sizes = torch.stack(
            [target["orig_size"] for target in labels], dim=0)
        results = image_processor.post_process_object_detection(
            outputs, target_sizes=orig_target_sizes)

        predictions = {target['image_id'].item(
        ): output for target, output in zip(labels, results)}
        predictions = prepare_for_coco_detection(predictions)
        evaluator.update(predictions)

    evaluator.synchronize_between_processes()
    evaluator.accumulate()
    evaluator.summarize()

    # Extraer métricas de AP y calcular el error
    ap_50 = evaluator.coco_eval['bbox'].stats[1]  # AP @ IoU=0.50

    # Error como complemento del AP
    error_50 = 1 - ap_50

    porcentaje_ap = ap_50 * 100
    porcentaje_error = error_50 * 100

    ruta_completa = os.path.join(directorioPersonalizado, "custom-model")

    # Guardar métricas en un archivo JSON
    metricas = {
        "tiempo_formateado": tiempo_formateado,
        "ap_50": porcentaje_ap,
        "error_50": porcentaje_error,
        "direccion": ruta_completa
    }
    direccionJson = os.path.join(directorioPersonalizado, "metricas.json")
    with open(direccionJson, 'w') as json_file:
        json.dump(metricas, json_file, indent=4)

    model.model.save_pretrained(directorioPersonalizado)

    model = DetrForObjectDetection.from_pretrained(directorioPersonalizado)
    model.to(DEVICE)
