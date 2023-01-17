Step-by-Step
============

This example load a face recognition model from [ONNX Model Zoo](https://github.com/onnx/models) and confirm its accuracy and speed based on [Refined MS-Celeb-1M](https://s3.amazonaws.com/onnx-model-zoo/arcface/dataset/faces_ms1m_112x112.zip).

# Prerequisite

## 1. Environment
onnx: 1.12.0  
onnxruntime: 1.13.1
> Validated framework versions can be found in main readme.

## 2. Prepare Model
Download model from [ONNX Model Zoo](https://github.com/onnx/models).

```shell
wget https://github.com/onnx/models/raw/main/vision/body_analysis/arcface/model/arcfaceresnet100-11.onnx
```

## 3. Prepare Dataset
Download dataset [Refined MS-Celeb-1M](https://s3.amazonaws.com/onnx-model-zoo/arcface/dataset/faces_ms1m_112x112.zip).

# Run

## 1. Quantization

```bash
bash run_tuning.sh --input_model=path/to/model \  # model path as *.onnx
                   --dataset_location=/path/to/faces_ms1m_112x112/task.bin \
                   --output_model=path/to/save
```

## 2. Benchmark

```bash
bash run_benchmark.sh --input_model=path/to/model \  # model path as *.onnx
                      --dataset_location=/path/to/faces_ms1m_112x112/task.bin \
                      --mode=performance # or accuracy
```
