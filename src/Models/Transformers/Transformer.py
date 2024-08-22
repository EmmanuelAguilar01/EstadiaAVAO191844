import os
import warnings
import random
import supervision as sv
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

warnings.filterwarnings(
    "ignore", message="`resume_download` is deprecated * ", category=FutureWarning)
warnings.filterwarnings(
    "ignore", message="The `max_size` parameter is deprecated", category=FutureWarning)

# settings
DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
CHECKPOINT = 'facebook/detr-resnet-50'
CONFIDENCE_TRESHOLD = 0.5
IOU_TRESHOLD = 0.8

image_processor = DetrImageProcessor.from_pretrained(CHECKPOINT)
model = DetrForObjectDetection.from_pretrained(CHECKPOINT)
model.to(DEVICE)


class Dataset:
    def __init__(self, location):
        self.location = location


dataset = Dataset(
    "C:/Users/nayel/Desktop/Estadia - AVAO191844/hackathone.v2i.coco")

ANNOTATION_FILE_NAME = "annotations.json"
TRAIN_DIRECTORY = os.path.join(dataset.location, "train")
VAL_DIRECTORY = os.path.join(dataset.location, "valid")
TEST_DIRECTORY = os.path.join(dataset.location, "test")


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


if __name__ == "__main__":
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
    detections = sv.Detections.from_coco_annotations(
        coco_annotation=annotations)

    # we will use id2label function for training
    categories = TRAIN_DATASET.coco.cats
    id2label = {k: v['name'] for k, v in categories.items()}

    labels = [
        f"{id2label[class_id]}"
        for _, _, class_id, _
        in detections
    ]

    box_annotator = sv.BoxAnnotator()
    frame = box_annotator.annotate(
        scene=image, detections=detections, labels=labels)

    TRAIN_DATALOADER = DataLoader(
        dataset=TRAIN_DATASET, collate_fn=collate_fn, batch_size=4, shuffle=True)
    VAL_DATALOADER = DataLoader(
        dataset=VAL_DATASET, collate_fn=collate_fn, batch_size=4)
    TEST_DATALOADER = DataLoader(
        dataset=TEST_DATASET, collate_fn=collate_fn, batch_size=4)

    model = Detr(lr=1e-4, lr_backbone=1e-5, weight_decay=1e-4)

    batch = next(iter(TRAIN_DATALOADER))
    outputs = model(pixel_values=batch['pixel_values'],
                    pixel_mask=batch['pixel_mask'])

    outputs.logits.shape

    # settings
    MAX_EPOCHS = 20

    trainer = Trainer(devices=1, accelerator="cpu", max_epochs=MAX_EPOCHS,
                      gradient_clip_val=0.1, accumulate_grad_batches=8, log_every_n_steps=5)

    trainer.fit(model)

    CHECKP_DIR = "C:\\Users\\nayel\\Desktop\\Estadia - AVAO191844\\Sistema\\src\\Checkpoints"
    CHECKPOINT_PATH = os.path.join(CHECKP_DIR, "PuntoGuardadoTrans.ckpt")

    trainer.save_checkpoint(CHECKPOINT_PATH)

    model.to(DEVICE)

    # utils
    categories = TEST_DATASET.coco.cats
    id2label = {k: v['name'] for k, v in categories.items()}
    box_annotator = sv.BoxAnnotator()

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
    detections = sv.Detections.from_coco_annotations(
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
    detections = sv.Detections.from_transformers(
        transformers_results=results).with_nms(threshold=0.5)
    labels = [f"{id2label[class_id]} {confidence:.2f}" for _,
              confidence, class_id, _ in detections]
    frame = box_annotator.annotate(
        scene=image.copy(), detections=detections, labels=labels)

    print('detections')

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

    MODEL_PATH = (
        r"C:\Users\nayel\Desktop\Estadia - AVAO191844\Sistema\src\Pesos")
    model.model.save_pretrained(MODEL_PATH)

    model = DetrForObjectDetection.from_pretrained(MODEL_PATH)
    model.to(DEVICE)
