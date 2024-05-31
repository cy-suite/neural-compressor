Quantization
===============

1. Quantization   
   1.1 [Quantization Introduction](#quantization-introduction)   
   1.2 [Quantization Fundamentals](#quantization-fundamentals)   
   1.3 [Accuracy Aware Tuning](#accuracy-aware-tuning)   
2. [Smooth Quant](#smooth-quant)   
3. [WOQ](#woq)   

## Quantization Introduction

Quantization is a very popular deep learning model optimization technique invented for improving the speed of inference. It minimizes the number of bits required by converting a set of real-valued numbers into the lower bit data representation, such as int8 and int4, mainly on inference phase with minimal to no loss in accuracy. This way reduces the memory requirement, cache miss rate, and computational cost of using neural networks and finally achieve the goal of higher inference performance. On Intel 3rd Gen Intel® Xeon® Scalable Processors, user could expect up to 4x theoretical performance speedup. We expect further performance improvement with [Intel® Advanced Matrix Extensions](https://www.intel.com/content/www/us/en/products/docs/accelerator-engines/advanced-matrix-extensions/overview.html) on 4th Gen Intel® Xeon® Scalable Processors.

## Quantization Fundamentals

`Affine quantization` and `Scale quantization` are two common range mapping techniques used in tensor conversion between different data types.

The math equation is like: $$X_{int8} = round(Scale \times X_{fp32} + ZeroPoint)$$.

**Affine Quantization**

This is so-called `asymmetric quantization`, in which we map the min/max range in the float tensor to the integer range. Here int8 range is [-128, 127], uint8 range is [0, 255]. 

here:

If INT8 is specified, $Scale = (|X_{f_{max}} - X_{f_{min}}|) / 127$ and $ZeroPoint = -128 - X_{f_{min}} / Scale$.

or

If UINT8 is specified, $Scale = (|X_{f_{max}} - X_{f_{min}}|) / 255$ and $ZeroPoint = - X_{f_{min}} / Scale$.

**Scale Quantization**

This is so-called `Symmetric quantization`, in which we use the maximum absolute value in the float tensor as float range and map to the corresponding integer range. 

The math equation is like:

here:

If INT8 is specified, $Scale = max(abs(X_{f_{max}}), abs(X_{f_{min}})) / 127$ and $ZeroPoint = 0$. 

or

If UINT8 is specified, $Scale = max(abs(X_{f_{max}}), abs(X_{f_{min}})) / 255$ and $ZeroPoint = 128$.

*NOTE*

Sometimes the reduce_range feature, that's using 7 bit width (1 sign bit + 6 data bits) to represent int8 range, may be needed on some early Xeon platforms, it's because those platforms may have overflow issues due to fp16 intermediate calculation result when executing int8 dot product operation. After AVX512_VNNI instruction is introduced, this issue gets solved by supporting fp32 intermediate data.



#### Quantization Scheme in TensorFlow
+ Symmetric Quantization
    + int8: scale = 2 * max(abs(rmin), abs(rmax)) / (max(int8) - min(int8) - 1)
    + uint8: scale = max(rmin, rmax) / (max(uint8) - min(uint8))

#### Quantization Scheme in PyTorch
+ Symmetric Quantization
    + int8: scale = max(abs(rmin), abs(rmax)) / (float(max(int8) - min(int8)) / 2)
    + uint8: scale = max(abs(rmin), abs(rmax)) / (float(max(int8) - min(int8)) / 2)
+ Asymmetric Quantization
    + uint8: scale = (rmax - rmin) / (max(uint8) - min(uint8)); zero_point = min(uint8)  - round(rmin / scale)

#### Quantization Scheme in IPEX
+ Symmetric Quantization
    + int8: scale = 2 * max(abs(rmin), abs(rmax)) / (max(int8) - min(int8) - 1)
    + uint8: scale = max(rmin, rmax) / (max(uint8) - min(uint8))

### Quantization Approaches

Quantization has three different approaches:
1) post training dynamic quantization
2) post training static  quantization
3) quantization aware training.

The first two approaches belong to optimization on inference. The last belongs to optimization during training.

#### Post Training Dynamic Quantization

The weights of the neural network get quantized into int8 format from float32 format offline. The activations of the neural network is quantized as well with the min/max range collected during inference runtime.

This approach is widely used in dynamic length neural networks, like NLP model.

#### Post Training Static Quantization

Compared with `post training dynamic quantization`, the min/max range in weights and activations are collected offline on a so-called `calibration` dataset. This dataset should be able to represent the data distribution of those unseen inference dataset. The `calibration` process runs on the original fp32 model and dumps out all the tensor distributions for `Scale` and `ZeroPoint` calculations. Usually preparing 100 samples are enough for calibration.

This approach is major quantization approach people should try because it could provide the better performance comparing with `post training dynamic quantization`.

#### Quantization Aware Training

Quantization aware training emulates inference-time quantization in the forward pass of the training process by inserting `fake quant` ops before those quantizable ops. With `quantization aware training`, all weights and activations are `fake quantized` during both the forward and backward passes of training: that is, float values are rounded to mimic int8 values, but all computations are still done with floating point numbers. Thus, all the weight adjustments during training are made while aware of the fact that the model will ultimately be quantized; after quantizing, therefore, this method will usually yield higher accuracy than either dynamic quantization or post-training static quantization.

## Accuracy Aware Tuning

Accuracy aware tuning is one of unique features provided by Intel(R) Neural Compressor, compared with other 3rd party model compression tools. This feature can be used to solve accuracy loss pain points brought by applying low precision quantization and other lossy optimization methods. 

This tuning algorithm creates a tuning space by querying framework quantization capability and model structure, selects the ops to be quantized by the tuning strategy, generates quantized graph, and evaluates the accuracy of this quantized graph. The optimal model will be yielded if the pre-defined accuracy goal is met. The `autotune` serves as a main interface of this algorithm.

Neural compressor also support to quantize all quantizable ops without accuracy tuning, using `quantize_model` interface to achieve that. 

### Working Flow

For supported quantization methods for `accuracy aware tuning` and the detailed API usage, please refer to the document of [PyTorch](./pytorch.md) or [TensorFlow](./tensorflow.md) respectively.

User could refer to below chart to understand the whole tuning flow.

<img src="../source/imgs/accuracy_aware_tuning_flow.png" width=600 height=480 alt="accuracy aware tuning working flow">


# Smooth Quant


# WOQ
