import os
from copy import deepcopy

import pytest
import torch
from transformers import AutoModelForCausalLM

from neural_compressor.torch.algorithms.weight_only.hqq.config import HQQModuleConfig, QTensorConfig, hqq_global_option
from neural_compressor.torch.algorithms.weight_only.hqq.core import HQQLinear


def _common_cpu_test(nbits=4, group_size=64, quant_zero=True, quant_scale=False, scale_quant_group_size=128):
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
    device = "cpu"

    # Create HQQ Linear
    bs = 4
    in_features = 64
    out_features = 128
    float_linear = torch.nn.Linear(in_features=in_features, out_features=out_features)
    if hqq_global_option.use_half:
        print(f"hqq_global_option use half: {hqq_global_option.use_half}")
        float_linear = float_linear.half()
    float_linear.to(device)
    float_linear_copy = deepcopy(float_linear)
    hqq_linear = HQQLinear.from_float(float_linear_copy, quant_config=hqq_quant_config)

    # Forward
    input = torch.randn(bs, in_features, device=device)
    if hqq_global_option.use_half:
        input = input.half()
    float_output = float_linear(input)
    input_for_hqq = deepcopy(input)
    hqq_output = hqq_linear(input_for_hqq)
    hqq_output_2 = hqq_linear(input_for_hqq)
    torch.allclose(float_output, hqq_output, atol=0.5)
    torch.allclose(hqq_output, hqq_output_2)
    del float_linear, hqq_linear
    del float_output, hqq_output, hqq_output_2


class TestHQQCPU:

    @classmethod
    def setup_class(cls):
        torch.manual_seed(0)

    @pytest.fixture
    def force_use_cpu(self, monkeypatch):
        # Force use CPU
        monkeypatch.setenv("FORCE_DEVICE", "cpu")

    @pytest.fixture
    def force_not_half(self, monkeypatch):
        monkeypatch.setattr(hqq_global_option, "use_half", False)

    def test_hqq_quant(self, force_use_cpu, force_not_half):
        from neural_compressor.torch.quantization import convert, get_default_hqq_config, prepare, quantize

        hqq_global_option.use_half = False
        fp32_model = AutoModelForCausalLM.from_pretrained("facebook/opt-125m")
        example_inputs = torch.tensor([[10, 20, 30, 40, 50, 60]], dtype=torch.long, device="cpu")
        # test_default_config
        quant_config = get_default_hqq_config()

        # prepare + convert API
        model = prepare(deepcopy(fp32_model), quant_config)
        model = convert(model)
        q_label_1 = model(example_inputs)[0]

        # quantize API
        model = quantize(deepcopy(fp32_model), quant_config)
        q_label_2 = model(example_inputs)[0]

        # compare the results of calling `convert` + `prepare` and calling `quantize`
        assert torch.all(
            q_label_1.eq(q_label_2)
        ), "The results of calling `convert` + `prepare` and calling `quantize` should be equal."

    def test_hqq_fallback(self, force_use_cpu, force_not_half):
        from neural_compressor.torch.quantization import HQQConfig, convert, prepare

        class ToyModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = torch.nn.Linear(128, 1024)
                self.fc2 = torch.nn.Linear(1024, 512)

            def forward(self, x):
                x = self.fc1(x)
                x = self.fc2(x)
                return x

        quant_config = HQQConfig().set_local("fc1", HQQConfig(dtype="fp32"))
        qmodel = convert(prepare(model=ToyModel(), quant_config=quant_config))
        assert type(qmodel.fc1).__name__ == torch.nn.Linear.__name__, f"Expect fallback fc1, but get {type(qmodel.fc1)}"
        assert type(qmodel.fc2).__name__ != torch.nn.Linear.__name__, f"Expect quantize fc2, but get {type(qmodel.fc2)}"

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
            (4, -1, False, True, 64),
        ],
    )
    def test_hqq_module_cpu(
        self, force_use_cpu, force_not_half, nbits, group_size, quant_zero, quant_scale, scale_quant_group_size
    ):
        _common_cpu_test(
            nbits=nbits,
            group_size=group_size,
            quant_zero=quant_zero,
            quant_scale=quant_scale,
            scale_quant_group_size=scale_quant_group_size,
        )


# _common_cpu_test(
#     nbits=4,
#     group_size=64,
#     quant_zero=False,
#     quant_scale=False,
#     scale_quant_group_size=128
# )
