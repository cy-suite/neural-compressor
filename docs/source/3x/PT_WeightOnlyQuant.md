
PyTorch Weight Only Quantization
===============
- [Introduction](#introduction)
- [Usage](#usage)
  - [Get Started](#get-started)
    - [RTN](#rtn)
    - [GPTQ](#gptq)
    - [AutoRound](#autoround)
    - [AWQ](#awq)
    - [TEQ](#teq)
    - [HQQ](#hqq)
  - [Specify Quantization Rules](#specify-quantization-rules)
  - [Saving and Loading](#saving-and-loading)
- [Examples](#examples)


## Introduction

The INC 3x New API provides support for quantizing PyTorch models using WeightOnlyQuant.

For detailed information on quantization fundamentals, please refer to the Quantization document [Quantization](../quantization.md)..


## Usage

### Get Started

The INC 3x New API supports quantizing PyTorch models using prepare and convert for WeightOnlyQuant quantization.

#### RTN

``` python
# Quantization code
from neural_compressor.torch.quantization import prepare, convert, RTNConfig

quant_config = RTNConfig()
model = prepare(model, quant_config)
model = convert(model)
```

#### GPTQ

``` python
# Quantization code
from neural_compressor.torch.quantization import prepare, convert, GPTQConfig

quant_config = GPTQConfig()
model = prepare(model, quant_config)
run_fn(model)  # calibration
model = convert(model)
```

#### AutoRound

``` python
# Quantization code
from neural_compressor.torch.quantization import prepare, convert, AutoRoundConfig

quant_config = AutoRoundConfig()
model = prepare(model, quant_config)
run_fn(model)  # calibration
model = convert(model)
```

#### AWQ

``` python
# Quantization code
from neural_compressor.torch.quantization import prepare, convert, AWQConfig

quant_config = AWQConfig()
model = prepare(model, quant_config, example_inputs=example_inputs)
run_fn(model)  # calibration
model = convert(model)
```

#### TEQ

``` python
# Quantization code
from neural_compressor.torch.quantization import prepare, convert, TEQConfig

quant_config = TEQConfig()
model = prepare(model, quant_config, example_inputs=example_inputs)
train_fn(model)  # calibration
model = convert(model)
```

#### HQQ

``` python
# Quantization code
from neural_compressor.torch.quantization import prepare, convert, HQQConfig

quant_config = HQQConfig()
model = prepare(model, quant_config)
run_fn(model)  # calibration
model = convert(model)
```
### Specify Quantization Rules
Intel(R) Neural Compressor support specify quantization rules by operator name or operator type. Users can set `local` in dict or use `set_local` method of config class to achieve the above purpose.

1. Example of setting `local` from a dict
```python
quant_config = {
    "rtn": {
        "global": {
            "dtype": "int",
            "bits": 4,
            "group_size": -1,
            "use_sym": True,
        },
        "local": {
            "lm_head": {
                "dtype": "fp32",
            },
        },
    }
}
```
2. Example of using `set_local`
```python
quant_config = RTNConfig()
lm_head_config = RTNConfig(dtype="fp32")
quant_config.set_local("lm_head", lm_head_config)
```

### Saving and Loading
The saved_results folder contains two files: quantized_model.pt and qconfig.json, and the generated model is a quantized model.
```python
# Quantization code
from neural_compressor.torch.quantization import prepare, convert, RTNConfig

quant_config = RTNConfig()
model = prepare(model, quant_config)
model = convert(model)

# save
model.save("saved_results")

# load
from neural_compressor.torch.quantization import load

orig_model = YOURMODEL()
loaded_model = load("saved_model", model=orig_model)  # Please note that the model parameter passes the original model.
```


## Examples

Users can also refer to [examples](https://github.com/intel/neural-compressor/blob/master/examples/3.x_api/pytorch/nlp/huggingface_models/language-modeling/quantization/llm) on how to quantize a  model with WeightOnlyQuant.
