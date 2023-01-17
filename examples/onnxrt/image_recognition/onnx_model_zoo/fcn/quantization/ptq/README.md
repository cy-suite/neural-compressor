Step-by-Step
============

This example load an object detection model converted from [ONNX Model Zoo](https://github.com/onnx/models) and confirm its accuracy and speed based on [MS COCO 2017 dataset](https://cocodataset.org/#download).

# Prerequisite

## 1. Environment
onnx: 1.12.0  
onnxruntime: 1.13.1
> Validated framework versions can be found in main readme.

## 2. Prepare Model
Download model from [ONNX Model Zoo](https://github.com/onnx/models).

```shell
wget https://github.com/onnx/models/raw/main/vision/object_detection_segmentation/fcn/model/fcn-resnet50-12.onnx
```

## 3. Prepare Dataset
Download dataset [MS COCO 2017 dataset](https://cocodataset.org/#download).

# Run

## 1. Quantization

Quantize model with QLinearOps:

```bash
bash run_tuning.sh --input_model=path/to/model  \ # model path as *.onnx
                   --dataset_location=path/to/coco/val2017 \
                   --output_model=path/to/save
```

Quantize model with QDQ mode:

```bash
bash run_tuning.sh --input_model=path/to/model  \ # model path as *.onnx
                   --dataset_location=path/to/coco/val2017 \
                   --output_model=path/to/save \
                   --quant_format=QDQ
```


## 2. Benchmark

```bash
bash run_benchmark.sh --input_model=path/to/model \  # model path as *.onnx
                      --dataset_location=path/to/coco/val2017 \
                      --mode=performance # or accuracy
```
