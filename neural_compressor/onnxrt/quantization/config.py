#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Intel Corporation
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

import re
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple, Union

import numpy as np
import onnx
from onnxruntime.quantization.calibrate import CalibrationMethod
from onnxruntime.quantization.quant_utils import QuantFormat, QuantType
from onnxruntime.quantization.quantize import StaticQuantConfig

from neural_compressor.common import Logger
from neural_compressor.common.base_config import BaseConfig, register_config, register_supported_configs_for_fwk
from neural_compressor.common.utils import DEFAULT_WHITE_LIST, OP_NAME_OR_MODULE_TYPE, RTN, SMOOTH_QUANT
from neural_compressor.onnxrt.utils import PRIORITY_SMOOTH_QUANT

logger = Logger().get_logger()

FRAMEWORK_NAME = "onnxrt"


class OperatorConfig(NamedTuple):
    config: BaseConfig
    operators: List[Union[str, Callable]]
    valid_func_list: List[Callable] = []


######################## RNT Config ###############################


@register_config(framework_name=FRAMEWORK_NAME, algo_name=RTN)
class RTNConfig(BaseConfig):
    """Config class for round-to-nearest weight-only quantization."""

    supported_configs: List[OperatorConfig] = []
    node_params_list = [
        "weight_dtype",
        "weight_bits",
        "weight_group_size",
        "weight_sym",
        "act_dtype",
        "accuracy_level",
    ]
    model_params_list = ["providers"]
    params_list = node_params_list + model_params_list
    name = RTN

    def __init__(
        self,
        weight_dtype: str = "int",
        weight_bits: int = 4,
        weight_group_size: int = 32,
        weight_sym: bool = True,
        act_dtype: str = "fp32",
        accuracy_level: int = 0,
        providers: list = ["CPUExecutionProvider"],
        white_list: Optional[List[OP_NAME_OR_MODULE_TYPE]] = DEFAULT_WHITE_LIST,
    ):
        """Init RTN weight-only quantization config.

        Args:
            weight_dtype (str): Data type for weights, default is "int".
            weight_bits (int): Number of bits used to represent weights, default is 4.
            weight_group_size (int): Size of weight groups, default is 32.
            weight_sym (bool): Indicates whether weights are symmetric, default is True.
            act_dtype (str): Data type for activations, default is "fp32".
        """
        super().__init__(white_list=white_list)
        self.weight_bits = weight_bits
        self.weight_dtype = weight_dtype
        self.weight_group_size = weight_group_size
        self.weight_sym = weight_sym
        self.act_dtype = act_dtype
        self.accuracy_level = accuracy_level
        self.providers = providers
        self._post_init()

    def get_model_params_dict(self):
        result = dict()
        for param in self.model_params_list:
            result[param] = getattr(self, param)
        return result

    @classmethod
    def register_supported_configs(cls) -> List[OperatorConfig]:
        supported_configs = []
        linear_rtn_config = RTNConfig(
            weight_dtype=["int"],
            weight_bits=[4, 3, 8],
            weight_group_size=[32, -1, 1, 16, 64, 128, 256, 512, 1024],
            weight_sym=[True, False],
            act_dtype=["fp32"],
        )
        operators = ["MatMul"]
        supported_configs.append(OperatorConfig(config=linear_rtn_config, operators=operators))
        cls.supported_configs = supported_configs

    def to_config_mapping(self, config_list: List[BaseConfig] = None, model_info: List[Tuple[str, str]] = None):
        config_mapping = OrderedDict()
        if config_list is None:
            config_list = [self]
        for config in config_list:
            # update model level setting
            config_mapping.update(config.get_model_params_dict())

            # update node level setting
            global_config = config.global_config
            op_type_config_dict, op_name_config_dict = config._get_op_name_op_type_config()
            for op_name, op_type in model_info:
                if self.global_config is not None:
                    config_mapping[(op_name, op_type)] = global_config
                if op_type in op_type_config_dict:
                    config_mapping[(op_name, op_type)] = op_name_config_dict[op_type]
                for op_name_pattern in op_name_config_dict:
                    if re.match(op_name_pattern, op_name):
                        config_mapping[(op_name, op_type)] = op_name_config_dict[op_name_pattern]
        return config_mapping

    @staticmethod
    def get_model_info(model: Union[onnx.ModelProto, Path, str]) -> List[Tuple[str, Callable]]:
        if not isinstance(model, onnx.ModelProto):
            model = onnx.load(model)
        white_list = ["MatMul"]
        filter_result = []
        for node in model.graph.node:
            if node.op_type in white_list:
                pair = (node.name, node.op_type)
                filter_result.append(pair)
        logger.debug(f"Get model info: {filter_result}")
        return filter_result

    @classmethod
    def get_config_set_for_tuning(cls) -> Union[None, "RTNConfig", List["RTNConfig"]]:  # pragma: no cover
        # TODO fwk owner needs to update it.
        return RTNConfig(weight_bits=[4, 6])


register_supported_configs_for_fwk(fwk_name=FRAMEWORK_NAME)


def get_default_rtn_config() -> RTNConfig:
    """Generate the default rtn config.

    Returns:
        the default rtn config.
    """
    return RTNConfig()


######################## SmoohQuant Config ###############################


@register_config(framework_name=FRAMEWORK_NAME, algo_name=SMOOTH_QUANT, priority=PRIORITY_SMOOTH_QUANT)
class SmoohQuantConfig(BaseConfig, StaticQuantConfig):
    """Smooth quant quantization config."""

    supported_configs: List[OperatorConfig] = []
    params_list = [
        # smooth parameters
        "alpha",
        "folding",
        "auto_alpha_args",
        "calib_iter",
        "scales_per_op",
        "op_types",
        "providers",
        # quant parameters
        "calibrate_method",
        "quant_format",
        "activation_type",
        "weight_type",
        "op_types_to_quantize",
        "nodes_to_quantize",
        "nodes_to_exclude",
        "per_channel",
        "reduce_range",
        "use_external_data_format",
        "extra_options",
    ]
    name = SMOOTH_QUANT

    def __init__(
        self,
        alpha: float = 0.5,
        folding: bool = True,
        op_types: list = ["Gemm", "Conv", "MatMul", "FusedConv"],
        calib_iter: int = 100,
        scales_per_op: bool = True,
        auto_alpha_args: Dict = {"alpha_min": 0.3, "alpha_max": 0.7, "alpha_step": 0.05, "attn_method": "min"},
        providers: list = ["CPUExecutionProvider"],
        white_list: Optional[List[OP_NAME_OR_MODULE_TYPE]] = DEFAULT_WHITE_LIST,
        **kwargs,
    ):
        """Init smooth quant config.

        Args:
            alpha (float or str): alpha value to balance the quantization difficulty of activation and weight.
            folding (bool): whether fold those foldable Mul which are inserted for smooth quant.
            op_types (list): the op type to be smooth quantized.
            calib_iter (int): iteration num for calibration.
            scales_per_op (bool): True, each op will have an individual scale, mainlyfor accuracy.
                                  False, ops with the same input will share a scale, mainly for performance.
            auto_alpha_args (dict): settings for alpha tuning.
            providers (list): providers used for inference.
            kwargs (dict): kwargs in below link are supported except calibration_data_reader:
                           https://github.com/microsoft/onnxruntime/blob/main/onnxruntime/python/tools/quantization/quantize.py#L78
        """
        BaseConfig.__init__(self)
        StaticQuantConfig.__init__(self, calibration_data_reader=None, **kwargs)
        self.alpha = alpha
        self.folding = folding
        self.op_types = op_types
        self.calib_iter = calib_iter
        self.scales_per_op = scales_per_op
        self.auto_alpha_args = auto_alpha_args
        self.providers = providers
        self.white_list = white_list
        self.weight_type = self.weight_type.value if isinstance(self.weight_type, Enum) else self.weight_type
        self.activation_type = (
            self.activation_type.value if isinstance(self.activation_type, Enum) else self.activation_type
        )
        self.calibrate_method = (
            self.calibrate_method.value if isinstance(self.calibrate_method, Enum) else self.calibrate_method
        )
        self.quant_format = self.quant_format.value if isinstance(self.quant_format, Enum) else self.quant_format
        self._post_init()

    @classmethod
    def register_supported_configs(cls) -> List[OperatorConfig]:
        supported_configs = []
        smooth_quant_config = SmoohQuantConfig()
        operators = ["Gemm", "Conv", "MatMul", "FusedConv"]
        supported_configs.append(OperatorConfig(config=smooth_quant_config, operators=operators))
        cls.supported_configs = supported_configs

    @staticmethod
    def get_model_info(model) -> List[Tuple[str, Callable]]:
        white_list = ["Gemm", "Conv", "MatMul", "FusedConv"]
        filter_result = []
        for node in model.graph.node:
            if node.op_type in white_list:
                pair = (node.name, node.op_type)
                filter_result.append(pair)
        logger.debug(f"Get model info: {filter_result}")
        return filter_result

    @classmethod
    def get_config_set_for_tuning(cls) -> Union[None, "SmoohQuantConfig", List["SmoohQuantConfig"]]:  # pragma: no cover
        # TODO fwk owner needs to update it.
        return SmoohQuantConfig(alpha=np.arange(0.3, 0.7, 0.05))

    def convert_to_ort_config(self):
        self.activation_type = QuantType(self.activation_type)
        self.weight_type = QuantType(self.weight_type)
        self.weight_type = QuantType(self.weight_type)
        self.calibrate_method = CalibrationMethod(self.calibrate_method)
        self.quant_format = QuantFormat(self.quant_format)


def get_default_sq_config() -> SmoohQuantConfig:
    """Generate the default smooth quant config.

    Returns:
        the default smooth quant config.
    """
    return SmoohQuantConfig()
