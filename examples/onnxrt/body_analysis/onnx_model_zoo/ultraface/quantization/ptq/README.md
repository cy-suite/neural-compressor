Step-by-Step
============

This example load an model converted from [ONNX Model Zoo](https://github.com/onnx/models) and confirm its accuracy and speed based on [WIDER FACE dataset (Validation Images)](http://shuoyang1213.me/WIDERFACE/).

# Prerequisite

## 1. Environment
onnx: 1.12.0  
onnxruntime: 1.13.1
> Validated framework versions can be found in main readme.

## 2. Prepare Model
Download model from [ONNX Model Zoo](https://github.com/onnx/models).

```shell
wget https://github.com/onnx/models/raw/main/vision/body_analysis/ultraface/models/version-RFB-320-12.onnx
```

## 3. Prepare Dataset
Download dataset [WIDER FACE dataset (Validation Images)](http://shuoyang1213.me/WIDERFACE/).

# Run

## 1. Quantization

```bash
bash run_tuning.sh --input_model=path/to/model  \ # model path as *.onnx
                   --dataset_location=/path/to/data \
                   --output_model=path/to/save
```

## 2. Benchmark

```bash
bash run_benchmark.sh --input_model=path/to/model \  # model path as *.onnx
                      --dataset_location=/path/to/data \
                      --mode=performance # or accuracy
```
