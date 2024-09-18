import shutil
from math import isclose

import pytest
import torch
from transformers import AutoTokenizer

from neural_compressor.transformers import (
    AutoModelForCausalLM,
    AutoRoundConfig,
    AwqConfig,
    GPTQConfig,
    RtnConfig,
    TeqConfig,
)


class TestTansformersLikeAPI:
    def setup_class(self):
        self.model_name_or_path = "hf-internal-testing/tiny-random-gptj"

    def teardown_class(self):
        shutil.rmtree("nc_workspace", ignore_errors=True)
        shutil.rmtree("transformers_tmp", ignore_errors=True)

    def test_quantization_for_llm(self):
        model_name_or_path = self.model_name_or_path
        tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)

        fp32_model = AutoModelForCausalLM.from_pretrained(model_name_or_path)
        dummy_input = fp32_model.dummy_inputs["input_ids"]
        label = fp32_model(dummy_input)[0]

        # weight-only
        # RTN
        woq_config = RtnConfig(bits=4, group_size=16)
        woq_model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=woq_config,
        )
        woq_model.eval()

        output = woq_model(dummy_input)[0]
        assert torch.allclose(output, label, atol=0.1), "Accuracy gap atol > 0.1 is unexpected."
        assert isclose(float(output[0][0][0]), 0.17786270380020142, rel_tol=1e-04)

        # AWQ
        woq_config = AwqConfig(
            bits=4, zero_point=False, n_samples=5, batch_size=1, seq_len=512, group_size=16, tokenizer=tokenizer
        )

        woq_model = AutoModelForCausalLM.from_pretrained(model_name_or_path, quantization_config=woq_config)
        woq_model.eval()
        output = woq_model(dummy_input)
        assert isclose(float(output[0][0][0][0]), 0.19592927396297455, rel_tol=1e-04)

        # TEQ
        woq_config = TeqConfig(bits=4, n_samples=5, batch_size=1, seq_len=512, group_size=16, tokenizer=tokenizer)
        woq_model = AutoModelForCausalLM.from_pretrained(model_name_or_path, quantization_config=woq_config)
        woq_model.eval()
        output = woq_model(dummy_input)
        assert isclose(float(output[0][0][0][0]), 0.17786270380020142, rel_tol=1e-04)

        # GPTQ
        woq_config = GPTQConfig(
            bits=4,
            weight_dtype="int4_clip",
            sym=True,
            desc_act=False,
            damp_percent=0.01,
            blocksize=32,
            n_samples=3,
            seq_len=256,
            tokenizer=tokenizer,
            batch_size=1,
            group_size=16,
        )
        woq_model = AutoModelForCausalLM.from_pretrained(model_name_or_path, quantization_config=woq_config)
        woq_model.eval()
        output = woq_model(dummy_input)
        assert isclose(float(output[0][0][0][0]), 0.17234990000724792, rel_tol=1e-04)

        # AUTOROUND
        woq_config = AutoRoundConfig(
            bits=4, weight_dtype="int4_clip", n_samples=128, seq_len=32, iters=5, group_size=16, tokenizer=tokenizer
        )
        woq_model = AutoModelForCausalLM.from_pretrained(model_name_or_path, quantization_config=woq_config)
        woq_model.eval()
        output = woq_model(dummy_input)
        assert isclose(float(output[0][0][0][0]), 0.18400897085666656, rel_tol=1e-04)

    def test_save_load(self):
        model_name_or_path = self.model_name_or_path

        fp32_model = AutoModelForCausalLM.from_pretrained(model_name_or_path)
        dummy_input = fp32_model.dummy_inputs["input_ids"]

        # RTN
        woq_config = RtnConfig(bits=4, group_size=16)
        woq_model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=woq_config,
        )
        woq_output = woq_model(dummy_input)[0]

        # save
        output_dir = "./transformers_tmp"
        woq_model.save_pretrained(output_dir)

        # load
        loaded_model = AutoModelForCausalLM.from_pretrained(output_dir)
        loaded_output = loaded_model(dummy_input)[0]
        assert torch.equal(woq_output, loaded_output), "loaded output should be same. Please double check."
