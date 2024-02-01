# Copyright (c) 2024 Intel Corporation
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

from typing import Dict, Tuple

import torch

from neural_compressor.common.utils import FP8_QUANT, GPTQ, RTN  # unified namespace
from neural_compressor.torch.algorithms.weight_only import gptq_quantize, rtn_quantize
from neural_compressor.torch.quantization import GPTQConfig, RTNConfig
from neural_compressor.torch.utils import logger, register_algo


###################### RTN Algo Entry ##################################
@register_algo(RTN)
@torch.no_grad()
def rtn_entry(
    model: torch.nn.Module, configs_mapping: Dict[Tuple[str, callable], RTNConfig], *args, **kwargs
) -> torch.nn.Module:
    """The main entry to apply rtn quantization."""
    # rebuild weight_config for rtn_quantize function
    weight_config = {}
    for (op_name, op_type), quant_config in configs_mapping.items():
        weight_config[op_name] = {
            "dtype": quant_config.dtype,
            "bits": quant_config.bits,
            "scheme": "sym" if quant_config.use_sym else "asym",
            "group_size": quant_config.group_size,
            "group_dim": quant_config.group_dim,
            "use_full_range": quant_config.use_full_range,
            "use_mse_search": quant_config.use_mse_search,
            "use_layer_wise": quant_config.use_layer_wise,
            "export_compressed_model": quant_config.export_compressed_model,
            "use_double_quant": quant_config.use_double_quant,
            "double_quant_dtype": quant_config.double_quant_dtype,
            "double_quant_bits": quant_config.double_quant_bits,
            "double_quant_scheme": "sym" if quant_config.double_quant_use_sym else "asym",
            "double_quant_group_size": quant_config.double_quant_group_size,
        }

    model = rtn_quantize(model, weight_config=weight_config)
    return model


###################### GPTQ Algo Entry ##################################
@register_algo(GPTQ)
@torch.no_grad()
def gptq_entry(
    model: torch.nn.Module, configs_mapping: Dict[Tuple[str, callable], GPTQConfig], *args, **kwargs
) -> torch.nn.Module:
    logger.info("Quantize model with the GPTQ algorithm.")

    model, quantization_perm = gptq_quantize(model=model, configs_mapping=configs_mapping, *args, **kwargs)
    # Assign the gptq config as an attribute of model
    model._gptq_quantization_perm = quantization_perm
    return model


###################### Habana FP8 Algo Entry ##################################
from neural_compressor.torch.utils import is_hpex_available

if is_hpex_available():
    from neural_compressor.torch.algorithms.habana_fp8 import quantize

    @register_algo(FP8_QUANT)
    def fp8_quant_entry(model, qconfig_mapping, run_fn=None, run_args=None, inplace=True):
        return quantize(model, qconfig_mapping, run_fn=run_fn, run_args=run_args, inplace=inplace)
