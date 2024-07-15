# Getting Started

1. [Quick Samples](#quick-samples)

2. [Feature Matrix](#feature-matrix)

## Quick Samples

```shell
# Install Intel Neural Compressor
pip install neural-compressor-pt
```
```python
from transformers import AutoModelForCausalLM
from neural_compressor.torch.quantization import RTNConfig, prepare, convert

user_model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-neo-125m")
quant_config = RTNConfig()
prepared_model = prepare(model=user_model, quant_config=quant_config)
quantized_model = convert(model=prepared_model)
```

## Feature Matrix
Intel Neural Compressor 3.X aim to provide framework extension APIs for the popular deep learning frameworks Torch and TensorFlow. 
The below table provides a quick overview of the APIs available in Intel Neural Compressor 3.X.
New API mainly focus on quantization related features especially for the algorithms benefit LLM inference. 
It also provides some common APIs across different frameworks. For example, Auto Tune API support accuracy driven quantization and mixed precision, benchmark API aimed to measure the multiple instances performance of the quantized model.

<table class="docutils">
  <thead>
  <tr>
    <th colspan="8">Overview</th>
  </tr>
  </thead>
  <tbody>
    <tr>
      <td colspan="2" align="center"><a href="design.md#architecture">Architecture</a></td>
      <td colspan="2" align="center"><a href="design.md#workflow">Workflow</a></td>
      <td colspan="2" align="center"><a href="https://intel.github.io/neural-compressor/latest/docs/source/api-doc/apis.html">APIs</a></td>
      <td colspan="1" align="center"><a href="llm_recipes.md">LLMs Recipes</a></td>
      <td colspan="1" align="center">Examples</td>
    </tr>
  </tbody>
  <thead>
    <tr>
      <th colspan="8">PyTorch Extension APIs</th>
    </tr>
  </thead>
  <tbody>
    <tr>
        <td colspan="2" align="center"><a href="PyTorch.md">Overview</a></td>
        <td colspan="2" align="center"><a href="PT_StaticQuant.md">Static Quantization</a></td>
        <td colspan="2" align="center"><a href="PT_DynamicQuant.md">Dynamic Quantization</a></td>
        <td colspan="2" align="center"><a href="PT_SmoothQuant.md">Smooth Quantization</a></td>
    </tr>
    <tr>
        <td colspan="3" align="center"><a href="PT_WeightOnlyQuant.md">Weight-Only Quantization</a></td>
        <td colspan="3" align="center"><a href="PT_MXQuant.md">MX Quantization</a></td>
        <td colspan="2" align="center"><a href="PT_MixedPrecision.md">Mixed Precision</a></td>
    </tr>
  </tbody>
  <thead>
      <tr>
        <th colspan="8">Tensorflow Extension APIs</th>
      </tr>
  </thead>
  <tbody>
      <tr>
          <td colspan="3" align="center"><a href="TensorFlow.md">Overview</a></td>
          <td colspan="3" align="center"><a href="TF_Quant.md">Static Quantization</a></td>
          <td colspan="2" align="center"><a href="TF_SQ.md">Smooth Quantization</a></td>
      </tr>
  </tbody>
  <thead>
      <tr>
        <th colspan="8">Common APIs</th>
      </tr>
  </thead>
  <tbody>
      <tr>
          <td colspan="4" align="center"><a href="autotune.md">Auto Tune</a></td>
          <td colspan="4" align="center"><a href="benchmark.md">Benchmark</a></td>
      </tr>
  </tbody>
</table>

> **Note**:   
> From 3.0 release, we recommended to use 3.X API, and the 2.X API will be deprecated in the future.  
> Documentations for 2.X API can be found at [2.X API User Guide](https://github.com/intel/neural-compressor/blob/master/docs/source/2x_user_guide.md).
