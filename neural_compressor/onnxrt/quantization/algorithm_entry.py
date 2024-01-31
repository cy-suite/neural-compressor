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

import tempfile
from pathlib import Path
from typing import Union

import onnx
from onnxruntime.quantization import quantize

from neural_compressor.common import Logger
from neural_compressor.common.utils import RTN, SMOOTH_QUANT
from neural_compressor.onnxrt.algorithms import Smoother
from neural_compressor.onnxrt.quantization.calibrate import CalibrationDataReader
from neural_compressor.onnxrt.quantization.config import RTNConfig, SmoohQuantConfig
from neural_compressor.onnxrt.utils.utility import register_algo

logger = Logger().get_logger()


###################### SmoothQuant Entry ##################################
@register_algo(name=SMOOTH_QUANT)
def smooth_quant_entry(
    model: Union[Path, str],
    quant_config: SmoohQuantConfig,
    calibration_data_reader: CalibrationDataReader,
    *args,
    **kwargs
) -> onnx.ModelProto:
    """Apply smooth quant."""
    assert calibration_data_reader is not None, "Please provide calibration_data_reader"
    assert isinstance(
        calibration_data_reader, CalibrationDataReader
    ), "Please follow neural_compressor/onnxrt/quantization/calibrate.py to implement calibration_data_reader"

    # smooth operation
    calibration_data_reader.rewind()
    smoother = Smoother(
        model,
        calibration_data_reader,
        providers=quant_config.providers,
    )
    smoothed_model = smoother.transform(**quant_config.to_dict())
    with tempfile.TemporaryDirectory(prefix="ort.quant.") as tmp_dir:
        # ORT quant API requires str input
        onnx.save_model(
            smoothed_model,
            Path(tmp_dir).joinpath("smooth.onnx").as_posix(),
            save_as_external_data=True,
            all_tensors_to_one_file=True,
            location="smooth.onnx_data",
            size_threshold=1024,
            convert_attribute=False,
        )

        # quant operation
        calibration_data_reader.rewind()

        # exclude Mul operations which are inserted during smooth operation
        excluded_nodes = [i.name for i in smoothed_model.graph.node if i.name.endswith("_smooth_mul")]
        quant_config.calibration_data_reader = calibration_data_reader
        quant_config.nodes_to_exclude.extend(excluded_nodes)
        quant_config.convert_to_ort_config()

        quantize(
            Path(tmp_dir).joinpath("smooth.onnx").as_posix(),
            Path(tmp_dir).joinpath("quant_model.onnx").as_posix(),
            quant_config,
        )
        model = onnx.load(Path(tmp_dir).joinpath("quant_model.onnx").as_posix())

    return model


###################### RTN Algo Entry ##################################
@register_algo(name=RTN)
def rtn_quantize_entry(model: Union[Path, str], quant_config: RTNConfig, *args, **kwargs) -> onnx.ModelProto:
    """The main entry to apply rtn quantization."""
    from neural_compressor.onnxrt.algorithms.weight_only.rtn import apply_rtn_on_model

    # map config to each op
    model_info = quant_config.get_model_info(model=model)
    configs_mapping = quant_config.to_config_mapping(model_info=model_info)
    logger.debug(configs_mapping)
    model = apply_rtn_on_model(model, configs_mapping)
    return model
