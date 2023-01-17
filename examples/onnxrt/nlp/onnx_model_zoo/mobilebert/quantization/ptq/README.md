Step-by-Step
============

This example load a language translation model and confirm its accuracy and speed based on [SQuAD]((https://rajpurkar.github.io/SQuAD-explorer/)) task.

# Prerequisite

## 1. Environment
onnx: 1.12.0  
onnxruntime: 1.13.1
> Validated framework versions can be found in main readme.

## 2. Prepare Model

Download pretrained bert model. We will refer to `vocab.txt` file.

```bash
wget https://storage.googleapis.com/bert_models/2018_10_18/uncased_L-12_H-768_A-12.zip
unzip uncased_L-12_H-768_A-12.zip
```

Download MLPerf mobilebert model and convert it to onnx model with [tf2onnx](https://github.com/onnx/tensorflow-onnx) tool.

```bash
wget https://github.com/fatihcakirs/mobile_models/raw/main/v0_7/tflite/mobilebert_float_384_20200602.tflite

python -m tf2onnx.convert --opset 11 --tflite mobilebert_float_384_20200602.tflite --output mobilebert_SQuAD.onnx
```

## 3. Prepare Dataset
Download SQuAD dataset from [SQuAD dataset link](https://rajpurkar.github.io/SQuAD-explorer/).

# Run

## 1. Quantization

Quantize model with dynamic quantization:

```bash
bash run_tuning.sh --input_model=/path/to/model \ # model path as *.onnx
                   --output_model=/path/to/model_tune \
                   --dataset_location=/path/to/SQuAD/dataset 
```

Quantize model with QDQ mode:

```bash
bash run_tuning.sh --input_model=/path/to/model \ # model path as *.onnx
                   --output_model=/path/to/model_tune \
                   --dataset_location=/path/to/SQuAD/dataset \
                   --quant_format='QDQ'
```

## 2. Benchmark

```bash
bash run_tuning.sh --input_model=/path/to/model \ # model path as *.onnx
                   --dataset_location=/path/to/SQuAD/dataset \
                   --batch_size=batch_size \
                   --mode=performance # or accuracy
```
