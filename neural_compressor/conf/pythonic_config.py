#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from .dotdict import DotDict
from ..config import ops_schema, AccuracyCriterion, accuracy_criterion, BenchmarkConfig, \
                     check_value, DistillationConfig, options, WeightPruningConfig

logger = logging.getLogger("neural_compressor")


class _BaseQuantizationConfig:
    """Args:
            inputs: inputs of model
            outputs: outputs of model
            backend: backend for model execution. Support 'default', 'itex', 'ipex', 'onnxrt_trt_ep', 'onnxrt_cuda_ep'
            domain: model domain. Support 'auto', 'cv', 'object_detection', 'nlp' and 'recommendation_system'.
                    Adaptor will use specific quantization settings for different domains automatically, and
                    explicitly specified quantization settings will override the automatic setting.
                    If users set domain as auto, automatic detection for domain will be executed.
            recipes: recipes for quantiztaion, support list is as below.
                     'smooth_quant': whether do smooth quant
                     'smooth_quant_args': parameters for smooth_quant
                     'fast_bias_correction': whether do fast bias correction
                     'weight_correction': whether do weight correction
                     'gemm_to_matmul': whether convert gemm to matmul and add, only valid for onnx models
                     'graph_optimization_level': support 'DISABLE_ALL', 'ENABLE_BASIC', 'ENABLE_EXTENDED', 'ENABLE_ALL'
                                               only valid for onnx models
                     'first_conv_or_matmul_quantization': whether quantize the first conv or matmul
                     'last_conv_or_matmul_quantization': whether quantize the last conv or matmul
                     'pre_post_process_quantization': whether quantize the ops in preprocess and postprocess
                     'add_qdq_pair_to_weight': whether add QDQ pair for weights, only vaild for onnxrt_trt_ep
                     'optypes_to_exclude_output_quant': don't quantize output of specified optypes
                     'dedicated_qdq_pair': whether dedicate QDQ pair, only vaild for onnxrt_trt_ep
            quant_format: support 'default', 'QDQ' and 'QOperator'
            device: support 'cpu' and 'gpu'
            calibration_sampling_size: number of calibration sample
            op_type_dict: tuning constraints on optype-wise
            op_name_dict: tuning constraints on op-wise
            strategy: strategy name
            strategy_kwargs: parameters for strategy
            objective: objective with accuracy constraint guaranteed, support 'performance', 'modelsize', 'footprint'
            timeout: tuning timeout (seconds). default value is 0 which means early stop
            max_trials: max tune times. default value is 100. Combine with timeout field to decide when to exit
            performance_only: whether do evaluation
            reduce_range: whether use 7 bit
            example_inputs: used to trace PyTorch model with torch.jit/torch.fx
            excluded_precisions: precisions to be excluded, support 'bf16'
            quant_level: support auto, 0 and 1, 0 is conservative strategy, 1 is basic or user-specified 
                         strategy, auto (default) is the combination of 0 and 1.
            accuracy_criterion: accuracy constraint settings
            use_distributed_tuning: whether use distributed tuning or not
    """
    def __init__(self,
                 inputs=[],
                 outputs=[],
                 backend="default",
                 domain="auto",
                 recipes={},
                 quant_format="default",
                 device="cpu",
                 calibration_sampling_size=[100],
                 op_type_dict=None,
                 op_name_dict=None,
                 strategy="basic",
                 strategy_kwargs=None,
                 objective="performance",
                 timeout=0,
                 max_trials=100,
                 performance_only=False,
                 reduce_range=None,
                 example_inputs=None,
                 excluded_precisions=[],
                 quant_level="auto",
                 accuracy_criterion=accuracy_criterion,
                 use_distributed_tuning=False):
        """Initialize _BaseQuantizationConfig class.
        """
        self.inputs = inputs
        self.outputs = outputs
        self.backend = backend
        self.domain = domain
        self.recipes = recipes
        self.quant_format = quant_format
        self.device = device
        self.op_type_dict = op_type_dict
        self.op_name_dict = op_name_dict
        self.strategy = strategy
        self.strategy_kwargs = strategy_kwargs
        self.objective = objective
        self.timeout = timeout
        self.max_trials = max_trials
        self.performance_only = performance_only
        self.reduce_range = reduce_range
        self.excluded_precisions = excluded_precisions
        self.use_bf16 = "bf16" not in self.excluded_precisions
        self.accuracy_criterion = accuracy_criterion
        self.calibration_sampling_size = calibration_sampling_size
        self.quant_level = quant_level
        self.use_distributed_tuning=use_distributed_tuning
        self._example_inputs = example_inputs

    @property
    def domain(self):
        """Get domain."""
        return self._domain

    @domain.setter
    def domain(self, domain):
        """Set domain."""
        if check_value("domain", domain, str,
            ["auto", "cv", "object_detection", "nlp", "recommendation_system"]):
            self._domain = domain

    @property
    def recipes(self):
        """Get recipes."""
        return self._recipes

    @recipes.setter
    def recipes(self, recipes):
        """Set recipes."""
        if recipes is not None and not isinstance(recipes, dict):
            raise ValueError("recipes should be a dict.")

        def smooth_quant(val=None):
            if val is not None:
                return check_value("smooth_quant", val, bool)
            else:
                return False

        def smooth_quant_args(val=None):
            if val is not None:
                check_value("smooth_quant_args", val, dict)
                for k, v in val.items():
                    if k == "alpha":
                        check_value("alpha", v, float)
                return True
            else:
                return {}

        def fast_bias_correction(val=None):
            if val is not None:
                return check_value("fast_bias_correction", val, bool)
            else:
                return False

        def weight_correction(val=None):
            if val is not None:
                return check_value("weight_correction", val, bool)
            else:
                return False

        def gemm_to_matmul(val=None):
            if val is not None:
                return check_value("gemm_to_matmul", val, bool)
            else:
                return True

        def graph_optimization_level(val=None):
            if val is not None:
                return check_value("graph_optimization_level", val, str,
                    ["DISABLE_ALL", "ENABLE_BASIC", "ENABLE_EXTENDED", "ENABLE_ALL"])
            else:
                return None

        def first_conv_or_matmul_quantization(val=None):
            if val is not None:
                return check_value("first_conv_or_matmul_quantization", val, bool)
            else:
                return True

        def last_conv_or_matmul_quantization(val=None):
            if val is not None:
                return check_value("last_conv_or_matmul_quantization", val, bool)
            else:
                return True

        def pre_post_process_quantization(val=None):
            if val is not None:
                return check_value("pre_post_process_quantization", val, bool)
            else:
                return True

        def add_qdq_pair_to_weight(val=None):
            if val is not None:
                return check_value("add_qdq_pair_to_weight", val, bool)
            else:
                return False

        def optypes_to_exclude_output_quant(val=None):
            if val is not None:
                return isinstance(val, list)
            else:
                return []

        def dedicated_qdq_pair(val=None):
            if val is not None:
                return check_value("dedicated_qdq_pair", val, bool)
            else:
                return False
        
        RECIPES = {"smooth_quant": smooth_quant,
                   "smooth_quant_args": smooth_quant_args,
                   "fast_bias_correction": fast_bias_correction,
                   "weight_correction": weight_correction,
                   "gemm_to_matmul": gemm_to_matmul,
                   "graph_optimization_level": graph_optimization_level,
                   "first_conv_or_matmul_quantization": first_conv_or_matmul_quantization,
                   "last_conv_or_matmul_quantization": last_conv_or_matmul_quantization,
                   "pre_post_process_quantization": pre_post_process_quantization,
                   "add_qdq_pair_to_weight": add_qdq_pair_to_weight,
                   "optypes_to_exclude_output_quant": optypes_to_exclude_output_quant,
                   "dedicated_qdq_pair": dedicated_qdq_pair
                   }
        self._recipes = {}
        for k in RECIPES.keys():
            if k in recipes and RECIPES[k](recipes[k]):
                self._recipes.update({k: recipes[k]})
            else:
                self._recipes.update({k: RECIPES[k]()})

    @property
    def accuracy_criterion(self):
        return self._accuracy_criterion

    @accuracy_criterion.setter
    def accuracy_criterion(self, accuracy_criterion):
        if check_value("accuracy_criterion", accuracy_criterion, AccuracyCriterion):
            self._accuracy_criterion = accuracy_criterion

    @property
    def excluded_precisions(self):
        return self._excluded_precisions

    @excluded_precisions.setter
    def excluded_precisions(self, excluded_precisions):
        if check_value("excluded_precisions", excluded_precisions, str, ["bf16", "fp16"]):
            self._excluded_precisions = excluded_precisions
            self._use_bf16 = "bf16" not in excluded_precisions

    @property
    def quant_level(self):
        return self._quant_level

    @quant_level.setter
    def quant_level(self, quant_level):
        self._quant_level = quant_level

    @property
    def use_distributed_tuning(self):
        return self._use_distributed_tuning

    @use_distributed_tuning.setter
    def use_distributed_tuning(self, use_distributed_tuning):
        if check_value('use_distributed_tuning', use_distributed_tuning, bool):
            self._use_distributed_tuning = use_distributed_tuning

    @property
    def reduce_range(self):
        return self._reduce_range

    @reduce_range.setter
    def reduce_range(self, reduce_range):
        if reduce_range is None or check_value('reduce_range', reduce_range, bool):
            self._reduce_range = reduce_range

    @property
    def performance_only(self):
        return self._performance_only

    @performance_only.setter
    def performance_only(self, performance_only):
        if check_value('performance_only', performance_only, bool):
            self._performance_only = performance_only

    @property
    def max_trials(self):
        return self._max_trials

    @max_trials.setter
    def max_trials(self, max_trials):
        if check_value('max_trials', max_trials, int):
            self._max_trials = max_trials

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        if check_value('timeout', timeout, int):
            self._timeout = timeout

    @property
    def objective(self):
        return self._objective

    @objective.setter
    def objective(self, objective):
        if check_value('objective', objective, str,
            ['performance', 'accuracy', 'modelsize', 'footprint']):
            self._objective = objective

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy):
        if check_value('strategy', strategy, str,
            ['basic', 'mse', 'bayesian', 'random', 'exhaustive', 'sigopt', 'tpe', 'mse_v2', 'hawq_v2']):
            self._strategy = strategy

    @property
    def strategy_kwargs(self):
        return self._strategy_kwargs

    @strategy_kwargs.setter
    def strategy_kwargs(self, strategy_kwargs):
        self._strategy_kwargs = strategy_kwargs

    @property
    def op_name_dict(self):
        return self._op_name_dict

    @op_name_dict.setter
    def op_name_dict(self, op_name_dict):
        if op_name_dict is None:
            self._op_name_dict = op_name_dict
        elif isinstance(op_name_dict, dict):
            for k, v in op_name_dict.items():
                ops_schema.validate(v)
            self._op_name_dict = op_name_dict
        else:
            assert False, ("Type of op_name_dict should be dict but not {}, ".format(
                type(op_name_dict)))

    @property
    def op_type_dict(self):
        return self._op_type_dict

    @op_type_dict.setter
    def op_type_dict(self, op_type_dict):
        if op_type_dict is None:
            self._op_type_dict = op_type_dict
        elif isinstance(op_type_dict, dict):
            for k, v in op_type_dict.items():
                ops_schema.validate(v)
            self._op_type_dict = op_type_dict
        else:
            assert False, ("Type of op_type_dict should be dict but not {}".format(
                type(op_type_dict)))

    @property
    def calibration_sampling_size(self):
        return self._calibration_sampling_size

    @calibration_sampling_size.setter
    def calibration_sampling_size(self, sampling_size):
        if check_value('calibration_sampling_size', sampling_size, int):
            if isinstance(sampling_size, int):
                sampling_size =[sampling_size]
            self._calibration_sampling_size = sampling_size

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, device):
        if check_value('device', device, str, ['cpu', 'gpu']):
            self._device = device

    @property
    def quant_format(self):
        return self._quant_format

    @quant_format.setter
    def quant_format(self, quant_format):
        if check_value('quant_format', quant_format, str,
            ['default', 'QDQ', 'QOperator']):
            self._quant_format = quant_format

    @property
    def backend(self):
        return self._backend

    @backend.setter
    def backend(self, backend):
        if check_value('backend', backend, str, [
                'default', 'itex', 'ipex', 'onnxrt_trt_ep', 'onnxrt_cuda_ep']):
            self._backend = backend

    @property
    def outputs(self):
        return self._outputs

    @outputs.setter
    def outputs(self, outputs):
        if check_value('outputs', outputs, str):
            self._outputs = outputs

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, inputs):
        if check_value('inputs', inputs, str):
            self._inputs = inputs

    @property
    def example_inputs(self):
        """Get strategy_kwargs."""
        return self._example_inputs

    @example_inputs.setter
    def example_inputs(self, example_inputs):
        """Set example_inputs."""
        self._example_inputs = example_inputs


class QuantizationConfig(_BaseQuantizationConfig):
    def __init__(self,
                 inputs=[],
                 outputs=[],
                 backend='default',
                 device='cpu',
                 approach='post_training_static_quant',
                 calibration_sampling_size=[100],
                 op_type_dict=None,
                 op_name_dict=None,
                 strategy='basic',
                 strategy_kwargs=None,
                 objective='performance',
                 timeout=0,
                 max_trials=100,
                 performance_only=False,
                 reduce_range=None,
                 use_bf16=True,
                 quant_level="auto",
                 accuracy_criterion=accuracy_criterion,
                 use_distributed_tuning=False):
        excluded_precisions = ["bf16"] if not use_bf16 else []
        super().__init__(
            inputs=inputs,
            outputs=outputs,
            backend=backend,
            device=device,
            calibration_sampling_size=calibration_sampling_size,
            op_type_dict=op_type_dict,
            op_name_dict=op_name_dict,
            strategy=strategy,
            strategy_kwargs=strategy_kwargs,
            objective=objective,
            timeout=timeout,
            max_trials=max_trials,
            performance_only=performance_only,
            reduce_range=reduce_range,
            excluded_precisions=excluded_precisions,
            accuracy_criterion=accuracy_criterion,
            quant_level=quant_level,
            use_distributed_tuning=use_distributed_tuning
        )
        self.approach = approach

    @property
    def approach(self):
        return self._approach

    @approach.setter
    def approach(self, approach):
        if check_value(
            'approach', approach, str,
            ['post_training_static_quant', 'post_training_dynamic_quant', 'quant_aware_training']
        ):
            self._approach = approach

class WeightConf:
    def __init__(self, datatype=None, scheme=None, granularity=None, algorithm=None):
        self._datatype = datatype
        self._scheme = scheme
        self._granularity = granularity
        self._algorithm = algorithm

    @property
    def datatype(self):
        return self._datatype

    @datatype.setter
    def datatype(self, datatype):
        if check_value('datatype', datatype, str, ['fp32', 'bf16', 'uint8', 'int8']):
            self._datatype = datatype if isinstance(datatype, list) else [datatype]

    @property
    def scheme(self):
        return self._scheme

    @scheme.setter
    def scheme(self, scheme):
        if check_value('scheme', scheme, str, ['sym', 'asym']):
            self._scheme = scheme if isinstance(scheme, list) else [scheme]

    @property
    def granularity(self):
        return self._granularity

    @granularity.setter
    def granularity(self, granularity):
        if check_value('granularity', granularity, str, ['per_channel', 'per_tensor']):
            self._granularity = granularity if isinstance(granularity, list) else [granularity]

    @property
    def algorithm(self):
        return self._algorithm

    @algorithm.setter
    def algorithm(self, algorithm):
        if check_value('algorithm', algorithm, str, ['minmax', 'kl']):
            self._algorithm = algorithm if isinstance(algorithm, list) else [algorithm]

class ActivationConf(WeightConf):
    def __init__(self, datatype=None, scheme=None, granularity=None, algorithm=None):
        super().__init__(datatype, scheme, granularity, algorithm)

weight = WeightConf()
activation = ActivationConf()

class OpQuantConf:
    def __init__(self, op_type=None, weight=weight, activation=activation):
        self._op_type = op_type
        self._weight = weight
        self._activation = activation

    @property
    def op_type(self):
        return self._op_type

    @op_type.setter
    def op_type(self, op_type):
        if check_value('op_type', op_type, str):
            self._op_type = op_type

    @property
    def weight(self):
        return self._weight

    @property
    def activation(self):
        return self._activation

class MXNet:
    def __init__(self, precisions=None):
        self._precisions = precisions

    @property
    def precisions(self):
        return self._precisions

    @precisions.setter
    def precisions(self, precisions):
        if not isinstance(precisions, list):
            precisions = [precisions]
        if check_value('precisions', precisions, str, ['int8', 'uint8', 'fp32', 'bf16', 'fp16']):
            self._precisions = precisions

class ONNX(MXNet):
    def __init__(self, graph_optimization_level=None, precisions=None):
        super().__init__(precisions)
        self._graph_optimization_level = graph_optimization_level

    @property
    def graph_optimization_level(self):
        return self._graph_optimization_level

    @graph_optimization_level.setter
    def graph_optimization_level(self, graph_optimization_level):
        if check_value('graph_optimization_level', graph_optimization_level, str,
            ['DISABLE_ALL', 'ENABLE_BASIC', 'ENABLE_EXTENDED', 'ENABLE_ALL']):
            self._graph_optimization_level = graph_optimization_level

class TensorFlow(MXNet):
    def __init__(self, precisions=None):
        super().__init__(precisions)

class Keras(MXNet):
    def __init__(self, precisions=None):
        super().__init__(precisions)

class PyTorch(MXNet):
    def __init__(self, precisions=None):
        super().__init__(precisions)


class DyNASConfig:
    def __init__(self, supernet=None, metrics=None, population=50, num_evals=100000,
                 results_csv_path=None, dataset_path=None, batch_size=64):
        self.config = {
            'supernet': supernet,
            'metrics': metrics,
            'population': population,
            'num_evals': num_evals,
            'results_csv_path': results_csv_path,
            'dataset_path': dataset_path,
            'batch_size': batch_size,
        }

class NASConfig:
    def __init__(self, approach=None, search_space=None, search_algorithm=None,
                 metrics=[], higher_is_better=[], max_trials=3, seed=42, dynas=None):
        self._approach = approach
        self._search = DotDict({
            'search_space': search_space,
            'search_algorithm': search_algorithm,
            'metrics': metrics,
            'higher_is_better': higher_is_better,
            'max_trials': max_trials,
            'seed': seed
        })
        self.dynas = None
        if approach == 'dynas' and dynas:
            self.dynas = dynas.config

    @property
    def approach(self):
        return self._approach

    @approach.setter
    def approach(self, approach):
        self._approach = approach

    @property
    def search(self):
        return self._search

    @search.setter
    def search(self, search):
        self._search = search


quantization = QuantizationConfig()
benchmark = BenchmarkConfig()
pruning = WeightPruningConfig()
distillation = DistillationConfig(teacher_model=None)
nas = NASConfig()
onnxruntime_config = ONNX()
tensorflow_config = TensorFlow()
keras_config = Keras()
pytorch_config = PyTorch()
mxnet_config = MXNet()


class Config:
    def __init__(self,
                 quantization=quantization,
                 benchmark=benchmark,
                 options=options,
                 pruning=pruning,
                 distillation=distillation,
                 nas=nas,
                 onnxruntime=onnxruntime_config,
                 tensorflow=tensorflow_config,
                 pytorch=pytorch_config,
                 mxnet=mxnet_config,
                 keras=keras_config):
        self._quantization = quantization
        self._benchmark = benchmark
        self._options = options
        self._onnxruntime = onnxruntime
        self._pruning = pruning
        self._distillation = distillation
        self._nas = nas
        self._tensorflow = tensorflow
        self._pytorch = pytorch
        self._mxnet = mxnet
        self._keras = keras

    @property
    def distillation(self):
        return self._distillation

    @property
    def nas(self):
        return self._nas

    @property
    def tensorflow(self):
        return self._tensorflow

    @property
    def keras(self):
        return self._keras

    @property
    def pytorch(self):
        return self._pytorch

    @property
    def mxnet(self):
        return self._mxnet

    @property
    def pruning(self):
        return self._pruning

    @property
    def quantization(self):
        return self._quantization

    @property
    def benchmark(self):
        return self._benchmark

    @property
    def options(self):
        return self._options

    @property
    def onnxruntime(self):
        return self._onnxruntime

config = Config()
