Step-by-Step
============

This document is used to enable Tensorflow Keras models using Intel® Neural Compressor.
This example can run on Intel CPUs and GPUs.


## Prerequisite

### 1. Installation
```shell
# Install Intel® Neural Compressor
pip install neural-compressor
```
### 2. Install Tensorflow
```shell
pip install tensorflow
```
> Note: Supported Tensorflow [Version](../../../../../../../README.md).

### 3. Install Intel Extension for Tensorflow
#### Quantizing the model on Intel GPU
Intel Extension for Tensorflow is mandatory to be installed for quantizing the model on Intel GPUs.

```shell
pip install --upgrade intel-extension-for-tensorflow[gpu]
```
Please refer to the [Installation Guides](https://dgpu-docs.intel.com/installation-guides/ubuntu/ubuntu-focal-dc.html) for latest Intel GPU driver installation.
For any more details, please follow the procedure in [install-gpu-drivers](https://github.com/intel-innersource/frameworks.ai.infrastructure.intel-extension-for-tensorflow.intel-extension-for-tensorflow/blob/master/docs/install/install_for_gpu.md#install-gpu-drivers).

#### Quantizing the model on Intel CPU(Experimental)
Intel Extension for Tensorflow for Intel CPUs is experimental currently. It's not mandatory for quantizing the model on Intel CPUs.

```shell
pip install --upgrade intel-extension-for-tensorflow[cpu]
```

### 4. Prepare Dataset

  TensorFlow [models](https://github.com/tensorflow/models) repo provides [scripts and instructions](https://github.com/tensorflow/models/tree/master/research/slim#an-automated-script-for-processing-imagenet-data) to download, process and convert the ImageNet dataset to the TF records format.
  We also prepared related scripts in `imagenet_prepare` directory. To download the raw images, the user must create an account with image-net.org. If you have downloaded the raw data and preprocessed the validation data by moving the images into the appropriate sub-directory based on the label (synset) of the image. we can use below command ro convert it to tf records format.

  ```shell
  cd examples/tensorflow/image_recognition/keras_models/
  # convert validation subset
  bash prepare_dataset.sh --output_dir=/mobilenet_v2/quantization/ptq/data --raw_dir=/PATH/TO/img_raw/val/ --subset=validation
  # convert train subset
  bash prepare_dataset.sh --output_dir=/mobilenet_v2/quantization/ptq/data --raw_dir=/PATH/TO/img_raw/train/ --subset=train
  cd mobilenet_v2/quantization/ptq
  ```

### 5. Prepare Pretrained model

The pretrained model is provided by [Keras Applications](https://keras.io/api/applications/). prepare the model, Run as follow: 
 ```
python prepare_model.py   --output_model=/path/to/model
 ```
`--output_model ` the model should be saved as SavedModel format or H5 format.

## Quantization Config
The Quantization Config class has default parameters setting for running on Intel CPUs. If running this example on Intel GPUs, the 'backend' parameter should be set to 'itex' and the 'device' parameter should be set to 'gpu'.

```
config = PostTrainingQuantConfig(
    device="gpu",
    backend="itex",
    ...
    )
```

## Run Command
#### Tune
  ```shell
  bash run_tuning.sh --input_model=./path/to/model --output_model=./result --dataset_location=/path/to/evaluation/dataset
  ```

#### Benchmark
  ```shell
  bash run_benchmark.sh --input_model=./path/to/model --dataset_location=/path/to/evaluation/dataset --mode=performance
  bash run_benchmark.sh --input_model=./path/to/model --dataset_location=/path/to/evaluation/dataset --mode=accuracy
  ```
