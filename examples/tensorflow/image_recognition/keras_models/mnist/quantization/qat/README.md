Step-by-Step
============

This document is used to apply QAT to Tensorflow Keras models using Intel® Neural Compressor.
This example can run on Intel CPUs and GPUs.

## Prerequisite

### 1. Installation
```shell
# Install Intel® Neural Compressor
pip install neural-compressor
```
### 2. Install requirements
The Tensorflow and intel-extension-for-tensorflow is mandatory to be installed to run this QAT example.
The Intel Extension for Tensorflow for Intel CPUs is installed as default.
```shell
pip install -r requirements.txt
```
> Note: Supported Tensorflow [Version](../../../../../../../README.md).

### 3. Benchmarking the model on Intel GPU (Optional)

To run benchmark of the model on Intel GPUs, Intel Extension for Tensorflow for Intel GPUs is required.

```shell
pip install --upgrade intel-extension-for-tensorflow[gpu]
```

Please refer to the [Installation Guides](https://dgpu-docs.intel.com/installation-guides/ubuntu/ubuntu-focal-dc.html) for latest Intel GPU driver installation.
For any more details, please follow the procedure in [install-gpu-drivers](https://github.com/intel-innersource/frameworks.ai.infrastructure.intel-extension-for-tensorflow.intel-extension-for-tensorflow/blob/master/docs/install/install_for_gpu.md#install-gpu-drivers).

### 4. Prepare Pretrained model

The pretrained model is provided by [Keras Applications](https://keras.io/api/applications/). prepare the model, Run as follow: 
 ```

python prepare_model.py --output_model=/path/to/model
 ```
`--output_model ` the model should be saved as SavedModel format or H5 format.

## Run Command
  ```shell
  bash run_tuning.sh --input_model=./path/to/model --output_model=./result 
  bash run_benchmark.sh --input_model=./path/to/model --mode=performance --batch_size=32
  ```

Details of enabling Intel® Neural Compressor to apply QAT.
=========================

This is a tutorial of how to to apply QAT with Intel® Neural Compressor.
## User Code Analysis
1. User specifies fp32 *model* to apply quantization, the dataset is automatically downloaded. In this step, QDQ patterns will be inserted to the keras model, but the fp32 model will not be converted to a int8 model.

2. User specifies *model* with QDQ patterns inserted, evaluate function to run benchmark. The model we get from the previous step will be run on ITEX backend. Then, the model is going to be fused and inferred.

### Quantization Config
The Quantization Config class has default parameters setting for running on Intel CPUs. If running this example on Intel GPUs, the 'backend' parameter should be set to 'itex' and the 'device' parameter should be set to 'gpu'.

```
config = QuantizationAwareTrainingConfig(
    device="gpu",
    backend="itex",
    ...
    )
```

### Code update

After prepare step is done, we add quantization and benchmark code to generate quantized model and benchmark.

#### Tune
```python
    logger.info('start quantizing the model...')
    from neural_compressor import training, QuantizationAwareTrainingConfig
    config = QuantizationAwareTrainingConfig()
    # create a compression_manager instance to implement QAT
    compression_manager = training.prepare_compression(FLAGS.input_model, config)
    # QDQ patterns will be inserted to the input keras model
    compression_manager.callbacks.on_train_begin()
    # get the model with QDQ patterns inserted
    q_aware_model = compression_manager.model.model

    # training code defined by users
    q_aware_model.compile(optimizer='adam',
                loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
                metrics=['accuracy'])
    q_aware_model.summary()
    train_images_subset = train_images[0:1000]
    train_labels_subset = train_labels[0:1000]
    q_aware_model.fit(train_images_subset, train_labels_subset,
                    batch_size=500, epochs=1, validation_split=0.1)
    _, q_aware_model_accuracy = q_aware_model.evaluate(
                                    test_images, test_labels, verbose=0)
    print('Quant test accuracy:', q_aware_model_accuracy)

    # apply some post process steps and save the output model
    compression_manager.callbacks.on_train_end()
    compression_manager.save(FLAGS.output_model)
```
#### Benchmark
```python
    from neural_compressor.benchmark import fit
    from neural_compressor.model import Model
    from neural_compressor.config import BenchmarkConfig
    assert FLAGS.mode == 'performance' or FLAGS.mode == 'accuracy', \
    "Benchmark only supports performance or accuracy mode."

    # convert the quantized keras model to graph_def so that it can be fused by ITEX
    model = Model(FLAGS.input_model).graph_def
    if FLAGS.mode == 'performance':
        conf = BenchmarkConfig(cores_per_instance=4, num_of_instance=7)
        fit(model, conf, b_func=evaluate)
    elif FLAGS.mode == 'accuracy':
        accuracy = evaluate(model)
        print('Batch size = %d' % FLAGS.batch_size)
        print("Accuracy: %.5f" % accuracy)
```