Step-by-Step
============

This example load an object detection model converted from [ONNX Model Zoo](https://github.com/onnx/models) and confirm its accuracy and speed based on [cityscapes dataset](https://www.cityscapes-dataset.com/downloads/).

# Prerequisite

## 1. Environment
onnx: 1.12.0  
onnxruntime: 1.13.1
> Validated framework versions can be found in main readme.

## 2. Prepare Model

Download model from [ONNX Model Zoo](https://github.com/onnx/models).

```shell
wget https://github.com/onnx/models/raw/main/vision/object_detection_segmentation/duc/model/ResNet101-DUC-12.onnx
```

## 3. Prepare Dataset
Download SQuAD dataset from [SQuAD dataset link](https://rajpurkar.github.io/SQuAD-explorer/).

# Run

## 1. Quantization

Quantize model with QLinearOps:

```bash
bash run_tuning.sh --input_model=path/to/model  \ # model path as *.onnx
                   --dataset_location=/path/to/leftImg8bit/val \
                   --output_model=path/to/save
```

## 2. Benchmark

```bash
bash run_benchmark.sh --input_model=path/to/model \  # model path as *.onnx
                      --dataset_location=/path/to/leftImg8bit/val \
                      --mode=performance
```
