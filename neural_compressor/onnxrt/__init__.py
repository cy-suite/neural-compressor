# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from onnxruntime.quantization.calibrate import CalibrationMethod
from onnxruntime.quantization.quant_utils import QuantType, QuantFormat
from neural_compressor.onnxrt.utils.utility import register_algo
from neural_compressor.onnxrt.quantization import (
    rtn_quantize_entry,
    smooth_quant_entry,
    RTNConfig,
    get_default_rtn_config,
    SmoohQuantConfig,
    get_default_sq_config,
    CalibrationDataReader,
)

__all__ = [
    "register_algo",
    "rtn_quantize_entry",
    "smooth_quant_entry",
    "RTNConfig",
    "get_default_rtn_config",
    "SmoohQuantConfig",
    "get_default_sq_config",
    "CalibrationDataReader",
    "QuantType",
    "QuantFormat",
    "CalibrationMethod",
]
