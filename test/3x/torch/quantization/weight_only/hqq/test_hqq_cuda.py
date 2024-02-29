from copy import deepcopy

import pytest
import torch
from transformers import AutoModelForCausalLM

from neural_compressor.torch.algorithms.weight_only.hqq.config import HQQModuleConfig, QTensorConfig, hqq_global_option
from neural_compressor.torch.algorithms.weight_only.hqq.core import HQQLinear
from neural_compressor.torch.algorithms.weight_only.hqq.utility import see_cuda_memory_usage
from neural_compressor.torch.utils.auto_accelerator import auto_detect_accelerator


def _common_cuda_test(nbits=4, group_size=64, quant_zero=True, quant_scale=False, scale_quant_group_size=128):
    # Parse config
    weight_qconfig = QTensorConfig(
        nbits=nbits, channel_wise=True, group_size=group_size, optimize=True, round_zero=True if nbits == 4 else False
    )
    zero_qconfig = None
    if quant_zero:
        zero_qconfig = QTensorConfig(nbits=8, channel_wise=False, group_size=None, optimize=False)
    scale_qconfig = None
    if quant_scale:
        scale_qconfig = QTensorConfig(nbits=8, channel_wise=True, group_size=scale_quant_group_size, optimize=False)
    hqq_quant_config = HQQModuleConfig(weight=weight_qconfig, scale=scale_qconfig, zero=zero_qconfig)
    device = torch.cuda.current_device()

    # Create HQQ Linear
    bs = 4
    in_features = 64
    out_features = 128
    see_cuda_memory_usage(message="Before create float linear")
    float_linear = torch.nn.Linear(in_features=in_features, out_features=out_features)
    if hqq_global_option.use_half:
        float_linear = float_linear.half()
    see_cuda_memory_usage(message="After create float linear")
    float_linear.to(device)
    float_linear_copy = deepcopy(float_linear)
    see_cuda_memory_usage(message="After copy the float linear")
    hqq_linear = HQQLinear.from_float(float_linear_copy, quant_config=hqq_quant_config)
    see_cuda_memory_usage(message="After create hqq linear")

    # Forward
    input = torch.randn(bs, in_features, device=device)
    if hqq_global_option.use_half:
        input = input.half()
    float_output = float_linear(input)
    input_for_hqq = deepcopy(input)
    hqq_output = hqq_linear(input_for_hqq)
    hqq_output_2 = hqq_linear(input_for_hqq)
    float_qdq_diff = 0.1  # hard code it first
    torch.allclose(float_output, hqq_output, atol=float_qdq_diff)
    torch.allclose(hqq_output, hqq_output_2)
    del float_linear, hqq_linear
    del float_output, hqq_output, hqq_output_2
    see_cuda_memory_usage("At the end of test")


@pytest.mark.skipif(not torch.cuda.is_available(), reason="test requires a GPU")
class TestHQQCUDA:
    @classmethod
    def setup_class(cls):
        torch.manual_seed(0)
        torch.cuda.manual_seed(0)
        hqq_global_option.use_half = True

    def test_hqq_quant(self):
        from neural_compressor.torch.quantization import get_default_hqq_config, quantize

        model = AutoModelForCausalLM.from_pretrained("facebook/opt-125m")
        example_inputs = torch.tensor(
            [[10, 20, 30, 40, 50, 60]], dtype=torch.long, device=auto_detect_accelerator().current_device()
        )
        # test_default_config
        quant_config = get_default_hqq_config()
        model = quantize(model, quant_config)
        q_label = model(example_inputs)[0]
        print(q_label)

    @pytest.mark.parametrize(
        "nbits, group_size, quant_zero, quant_scale, scale_quant_group_size",
        [
            (4, 64, True, False, 128),
            (4, 64, False, False, 128),
            (4, 64, True, True, 128),
            (4, 64, False, True, 128),
            (8, 64, True, False, 128),
            (8, 64, False, False, 128),
            (8, 64, True, True, 128),
            (8, 64, False, True, 128),
            (4, 64, True, False, 64),
            (4, 64, False, False, 64),
            (4, 64, True, True, 64),
            (4, 64, False, True, 64),
        ],
    )
    def test_hqq_module_cuda(
        self,
        nbits,
        group_size,
        quant_zero,
        quant_scale,
        scale_quant_group_size,
    ):
        _common_cuda_test(
            nbits=nbits,
            group_size=group_size,
            quant_zero=quant_zero,
            quant_scale=quant_scale,
            scale_quant_group_size=scale_quant_group_size,
        )


# _common_cuda_test(
#     nbits=4,
#     group_size=64,
#     quant_zero=False,
#     quant_scale=False,
#     scale_quant_group_size=128
# )
