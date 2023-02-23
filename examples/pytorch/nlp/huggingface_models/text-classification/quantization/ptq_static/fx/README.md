Step-by-Step
============

This document is used to introduce steps of reproducing PyTorch BERT tuning zoo result.

> **Note**
>
> Dynamic Quantization is the recommended method for huggingface models. 

# Prerequisite

## Environment

Recommend python 3.6 or higher version.

```bash
pip install transformers
```

```shell
pip install -r requirements.txt
```

```shell
pip install torch
```
> Note: Validated PyTorch [Version](/docs/source/installation_guide.md#validated-software-environment).

## Prepare pretrained model

Before using Intel® Neural Compressor, it is recommend to fine-tune the model to get pretrained models or reuse fine-tuned models in [model hub](https://huggingface.co/models). The user should also install the additional packages required by the examples.

# Run
 - Here we implemented several models in fx mode.
```shell
cd examples/pytorch/nlp/huggingface_models/text-classification/quantization/ptq_static/fx
```
## Glue task

### 1. Get the tuned model and its accuracy: 
```bash
python -u ./run_glue.py \
        --model_name_or_path distilbert-base-uncased-finetuned-sst-2-english \
        --task_name sst2 \
        --do_eval \
        --do_train \
        --max_seq_length 128 \
        --per_device_eval_batch_size 16 \
        --no_cuda \
        --output_dir ./int8_model_dir \
        --tune \
        --overwrite_output_dir
``` 

You can also try to use INC distributed tuning (Take mrpc task as an example) as follows:

In `run_glue.py`, set `config.use_distributed_tuning` to True by the following statement.

```python
conf = PostTrainingQuantConfig(approach="static", tuning_criterion=tuning_criterion, use_distributed_tuning=True)
```

And then, run the following command:

```
mpirun -np <NUM_PROCESS> -mca btl_tcp_if_include <NETWORK_INTERFACE> -x OMP_NUM_THREADS=<MAX_NUM_THREADS> --host <HOSTNAME1>,<HOSTNAME2>,<HOSTNAME3> bash run_distributed_tuning.sh
```

* *`<NUM_PROCESS>`* is the number of processes, which is recommended to set to be equal to the number of hosts.

* *`<MAX_NUM_THREADS>`* is the number of threads, which is recommended to set to be equal to
the number of physical cores on one node.

* *`<HOSTNAME>`* is the host name, and argument `--host <HOSTNAME>,<HOSTNAME>...` can be replaced with `--hostfile <HOSTFILE>`, when each line in *`<HOSTFILE>`* is a host name.

* `-mca btl_tcp_if_include <NETWORK_INTERFACE>` is used to set the network communication interface between hosts. For example, *`<NETWORK_INTERFACE>`* can be set to 192.168.20.0/24 to allow the MPI communication between all hosts under the 192.168.20.* network segment.

### 2. Get the benchmark of the tuned model

```bash
python -u ./run_glue.py \
        --model_name_or_path ./int8_model_dir \
        --task_name sst2 \
        --do_eval \
        --max_seq_length 128 \
        --per_device_eval_batch_size 1 \
        --no_cuda \
        --output_dir ./output_log \
        --benchmark \
        --int8 \
        --overwrite_output_dir
```

# HuggingFace model hub
## Upstream model files into HuggingFace model hub
Intel® Neural Compressor provides an API `save_for_huggingface_upstream` to collect configuration files, tokenizer files and int8 model weights in the format of [transformers](https://github.com/huggingface/transformers). 
```
from neural_compressor.utils.load_huggingface import save_for_huggingface_upstream
...

save_for_huggingface_upstream(q_model, tokenizer, output_dir)
```
Users can upstream files in the `output_dir` into model hub and reuse them with our `OptimizedModel` API.

## Download into HuggingFace model hub
Intel® Neural Compressor provides an API `OptimizedModel` to initialize int8 models from HuggingFace model hub, and its usage is the same as the model class provided by [transformers](https://github.com/huggingface/transformers).
```python
from neural_compressor.utils.load_huggingface import OptimizedModel
model = OptimizedModel.from_pretrained(
            model_args.model_name_or_path,
            config=config,
            cache_dir=model_args.cache_dir,
            revision=model_args.model_revision,
            use_auth_token=True if model_args.use_auth_token else None,
        )
```

We have upstreamed several int8 models into HuggingFace [model hub](https://huggingface.co/models?other=Intel%C2%AE%20Neural%20Compressor) for users to ramp up.

----
----
## This is a tutorial about how to enable NLP model with Intel® Neural Compressor.


### Intel® Neural Compressor supports usage:
* User needs to specify fp32 'model', calibration dataset 'q_dataloader' and a custom "eval_func", which encapsulates the evaluation dataset and metrics by itself.

### Code Prepare

The updated run_glue.py is shown as below

```python
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset if training_args.do_train else None,
    eval_dataset=eval_dataset if training_args.do_eval else None,
    compute_metrics=compute_metrics,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

eval_dataloader = trainer.get_eval_dataloader()
batch_size = eval_dataloader.batch_size

metric_name = "eval_f1"
def take_eval_steps(model, trainer, metric_name, save_metrics=False):
    trainer.model = model
    metrics = trainer.evaluate()
    if save_metrics:
        trainer.save_metrics("eval", metrics)
    logger.info("{}: {}".format(metric_name, metrics.get(metric_name)))
    logger.info("Throughput: {} samples/sec".format(metrics.get("eval_samples_per_second")))
    return metrics.get(metric_name)
def eval_func(model):
    return take_eval_steps(model, trainer, metric_name)

from neural_compressor.quantization import fit
from neural_compressor.config import PostTrainingQuantConfig, TuningCriterion
tuning_criterion = TuningCriterion(max_trials=600)
conf = PostTrainingQuantConfig(approach="static", tuning_criterion=tuning_criterion)
q_model = fit(model, conf=conf, calib_dataloader=eval_dataloader, eval_func=eval_func)
from neural_compressor.utils.load_huggingface import save_for_huggingface_upstream
save_for_huggingface_upstream(q_model, tokenizer, training_args.output_dir)
```

# Appendix

## Export to ONNX

Right now, we experimentally support exporting PyTorch model to ONNX model, includes FP32 and INT8 model.

By enabling `--onnx` argument, Intel Neural Compressor will export fp32 ONNX model, INT8 QDQ ONNX model, and INT8 QLinear ONNX model.
