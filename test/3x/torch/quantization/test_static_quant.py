import copy
import shutil

import pytest
import torch

from neural_compressor.torch.quantization import (
    StaticQuantConfig,
    convert,
    get_default_static_config,
    prepare,
    quantize,
)
from neural_compressor.torch.utils import is_ipex_available

if is_ipex_available():
    import intel_extension_for_pytorch as ipex


def build_simple_torch_model():
    class Model(torch.nn.Module):
        def __init__(self):
            super(Model, self).__init__()
            self.fc1 = torch.nn.Linear(30, 50)
            self.fc2 = torch.nn.Linear(50, 30)
            self.fc3 = torch.nn.Linear(30, 5)

        def forward(self, x):
            out = self.fc1(x)
            out = self.fc2(out)
            out = self.fc3(out)
            return out

    model = Model()
    return model


def run_fn(model):
    model(torch.rand((1, 30)))
    model(torch.rand((1, 30)))


class TestStaticQuant:
    def setup_class(self):
        self.fp32_model = build_simple_torch_model()
        self.input = torch.randn(1, 30)

    def teardown_class(self):
        shutil.rmtree("saved_results", ignore_errors=True)

    @pytest.mark.skipif(not is_ipex_available(), reason="Requires IPEX")
    def test_static_quant_default(self):
        fp32_model = copy.deepcopy(self.fp32_model)
        quant_config = get_default_static_config()
        example_inputs = self.input
        prepared_model = prepare(fp32_model, quant_config=quant_config, example_inputs=example_inputs)
        run_fn(prepared_model)
        q_model = convert(prepared_model)
        assert q_model is not None, "Quantization failed!"

    @pytest.mark.skipif(not is_ipex_available(), reason="Requires IPEX")
    def test_static_quant_fallback(self):
        fp32_model = copy.deepcopy(self.fp32_model)
        quant_config = get_default_static_config()
        example_inputs = self.input
        # fallback by op_type
        quant_config.set_local(torch.nn.Linear, StaticQuantConfig(w_dtype="fp32", act_dtype="fp32"))
        prepared_model = prepare(fp32_model, quant_config=quant_config, example_inputs=example_inputs)
        run_fn(prepared_model)
        q_model = convert(prepared_model)
        assert q_model is not None, "Quantization failed!"

        for op, op_info in q_model.tune_cfg[" "]["q_op_infos"].items():
            if op_info["op_type"] == "<class 'torch.nn.modules.linear.Linear'>":
                dtype = q_model.tune_cfg[" "]["q_op_infos"][op]["input_tensor_infos"][0]["force_dtype"]
                assert dtype == "torch.float32", "Failed to fallback linear op, please check!"

        # fallback by op_name
        quant_config.set_local("fc1", StaticQuantConfig(w_dtype="fp32", act_dtype="fp32"))
        prepared_model = prepare(fp32_model, quant_config=quant_config, example_inputs=example_inputs)
        run_fn(prepared_model)
        q_model = convert(prepared_model)
        assert q_model is not None, "Quantization failed!"

        for op, op_info in q_model.tune_cfg[" "]["q_op_infos"].items():
            if op_info["fqn"] == "fc1":
                dtype = q_model.tune_cfg[" "]["q_op_infos"][op]["input_tensor_infos"][0]["force_dtype"]
                assert dtype == "torch.float32", "Failed to fallback fc1 layer, please check!"

    @pytest.mark.skipif(not is_ipex_available(), reason="Requires IPEX")
    @pytest.mark.parametrize(
        "act_sym, act_algo",
        [
            (True, "kl"),
            (True, "minmax"),
            (False, "kl"),
            (False, "minmax"),
        ],
    )
    def test_static_quant_params(self, act_sym, act_algo):
        fp32_model = copy.deepcopy(self.fp32_model)
        quant_config = StaticQuantConfig(act_sym=act_sym, act_algo=act_algo)
        example_inputs = self.input
        prepared_model = prepare(fp32_model, quant_config=quant_config, example_inputs=example_inputs)
        run_fn(prepared_model)
        q_model = convert(prepared_model)
        assert q_model is not None, "Quantization failed!"

    @pytest.mark.skipif(not is_ipex_available(), reason="Requires IPEX")
    def test_static_quant_accuracy(self):
        class M(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = torch.nn.Linear(2, 2, False)

            def forward(self, x):
                x = self.linear(x)
                x = x + x
                return x

        model = M()

        def run_fn(model):
            model(torch.randn(3, 2))

        fp32_model = copy.deepcopy(model)
        fp32_model.linear.weight = torch.nn.Parameter(torch.tensor([[0.0, 1.0], [1.0, 0.0]]))
        example_inputs = torch.zeros(3, 2)
        quant_config = StaticQuantConfig(act_sym=True, act_algo="kl")
        prepared_model = prepare(fp32_model, quant_config=quant_config, example_inputs=example_inputs)
        run_fn(prepared_model)
        q_model = convert(prepared_model)
        output1 = fp32_model(example_inputs)
        output2 = q_model(example_inputs)
        # set a big atol to avoid random issue
        assert torch.allclose(output1, output2, atol=2e-2), "Accuracy gap atol > 0.02 is unexpected. Please check."

    @pytest.mark.skipif(not is_ipex_available(), reason="Requires IPEX")
    def test_static_quant_save_load(self):
        from intel_extension_for_pytorch.quantization import convert as ipex_convert
        from intel_extension_for_pytorch.quantization import prepare as ipex_prepare

        example_inputs = torch.zeros(1, 30)
        try:
            qconfig = ipex.quantization.default_static_qconfig_mapping
        except:
            from torch.ao.quantization import MinMaxObserver, PerChannelMinMaxObserver, QConfig

            qconfig = QConfig(
                activation=MinMaxObserver.with_args(qscheme=torch.per_tensor_affine, dtype=torch.quint8),
                weight=PerChannelMinMaxObserver.with_args(dtype=torch.qint8, qscheme=torch.per_channel_symmetric),
            )
        user_model = copy.deepcopy(self.fp32_model)
        user_model = ipex_prepare(user_model.eval(), qconfig, example_inputs=example_inputs, inplace=True)

        def run_fn(model):
            model(example_inputs)

        run_fn(user_model)
        with torch.no_grad():
            user_model = ipex_convert(user_model.eval(), inplace=True).eval()
            user_model(example_inputs)
            user_model = torch.jit.trace(user_model.eval(), example_inputs, strict=False)
            user_model = torch.jit.freeze(user_model.eval())
            user_model(example_inputs)
            user_model(example_inputs)
        ipex_out = user_model(example_inputs)

        fp32_model = copy.deepcopy(self.fp32_model)
        quant_config = get_default_static_config()
        prepared_model = prepare(fp32_model, quant_config=quant_config, example_inputs=example_inputs)
        run_fn(prepared_model)
        q_model = convert(prepared_model)
        assert q_model is not None, "Quantization failed!"
        inc_out = q_model(example_inputs)
        # set a big atol to avoid random issue
        assert torch.allclose(inc_out, ipex_out, atol=2e-02), "Unexpected result. Please double check."
        q_model.save("saved_results")

        from neural_compressor.torch.algorithms.static_quant import load

        # load
        loaded_model = load("saved_results")
        assert isinstance(loaded_model, torch.jit.ScriptModule)

    @pytest.mark.skipif(not is_ipex_available(), reason="Requires IPEX")
    def test_static_quant_with_quantize_API(self):
        # quantize API
        fp32_model = copy.deepcopy(self.fp32_model)
        quant_config = get_default_static_config()
        example_inputs = self.input
        q_model = quantize(fp32_model, quant_config=quant_config, run_fn=run_fn, example_inputs=example_inputs)
        assert q_model is not None, "Quantization failed!"
