import copy
import unittest

import transformers

from neural_compressor.common.logger import Logger

logger = Logger().get_logger()
import torch


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


class TestQuantizationConfig(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.fp32_model = build_simple_torch_model()
        self.input = torch.randn(1, 30)
        self.gptj = transformers.AutoModelForCausalLM.from_pretrained(
            "hf-internal-testing/tiny-random-GPTJForCausalLM",
        )
        self.lm_input = torch.ones([1, 10], dtype=torch.long)

    @classmethod
    def tearDownClass(self):
        pass

    def setUp(self):
        # print the test name
        logger.info(f"Running TestQuantizationConfig test: {self.id()}")

    def test_quantize_rtn_from_dict_default(self):
        logger.info("test_quantize_rtn_from_dict_default")
        from neural_compressor.torch import get_default_rtn_config, quantize

        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config=get_default_rtn_config())
        self.assertIsNotNone(qmodel)

    def test_quantize_rtn_from_dict_beginner(self):
        from neural_compressor.torch import quantize

        quant_config = {
            "rtn_weight_only_quant": {
                "weight_dtype": "nf4",
                "weight_bits": 4,
                "weight_group_size": 32,
            },
        }
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_quantize_rtn_from_class_beginner(self):
        from neural_compressor.torch import RTNWeightQuantConfig, quantize

        quant_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="nf4", weight_group_size=32)
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_quantize_rtndq_from_class_beginner(self):
        from neural_compressor.torch import RTNWeightQuantConfig, quantize

        fp32_config = RTNWeightQuantConfig(weight_dtype="fp32")

        fp32_model = copy.deepcopy(self.gptj)
        quant_config = RTNWeightQuantConfig(
            weight_bits=4,
            weight_dtype="int",
            weight_sym=False,
            weight_group_size=32,
        )
        quant_config.set_local("lm_head", fp32_config)
        qmodel = quantize(fp32_model, quant_config)
        out2 = qmodel(self.lm_input)

        fp32_model = copy.deepcopy(self.gptj)
        # llama.cpp GGML_TYPE_Q4_K setting
        quant_config = RTNWeightQuantConfig(
            weight_bits=4,
            weight_dtype="int",
            weight_sym=False,
            weight_group_size=32,
            double_quant_bits=6,
            double_quant_dtype="int",
            double_quant_sym=True,
            double_quant_group_size=8,
        )
        quant_config.set_local("lm_head", fp32_config)
        qmodel = quantize(fp32_model, quant_config)
        out3 = qmodel(self.lm_input)
        self.assertTrue(torch.allclose(out3[0], out2[0], atol=1e-2))

        fp32_model = copy.deepcopy(self.gptj)

        quant_config = RTNWeightQuantConfig(
            weight_bits=4,
            weight_dtype="nf4",
            weight_group_size=32,
        )
        quant_config.set_local("lm_head", fp32_config)
        qmodel = quantize(fp32_model, quant_config)
        out4 = qmodel(self.lm_input)

        fp32_model = copy.deepcopy(self.gptj)
        # bitsandbytes double quant setting
        quant_config = RTNWeightQuantConfig(
            weight_bits=4,
            weight_dtype="nf4",
            weight_group_size=32,
            double_quant_dtype="int",
            double_quant_bits=8,
            double_quant_sym=False,
            double_quant_group_size=256,
        )
        quant_config.set_local("lm_head", fp32_config)
        qmodel = quantize(fp32_model, quant_config)
        out5 = qmodel(self.lm_input)
        self.assertTrue(torch.allclose(out4[0], out5[0], atol=1e-2))

    def test_quantize_rtn_from_dict_advance(self):
        from neural_compressor.torch import quantize

        fp32_model = build_simple_torch_model()
        quant_config = {
            "rtn_weight_only_quant": {
                "global": {
                    "weight_dtype": "nf4",
                    "weight_bits": 4,
                    "weight_group_size": 32,
                },
                "local": {
                    "fc1": {
                        "weight_dtype": "int8",
                        "weight_bits": 4,
                    }
                },
            }
        }
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_quantize_rtn_from_class_advance(self):
        from neural_compressor.torch import RTNWeightQuantConfig, quantize

        quant_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="nf4")
        # set operator instance
        fc1_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="int8")
        quant_config.set_local("model.fc1", fc1_config)
        # get model and quantize
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_config_white_lst(self):
        from neural_compressor.torch import RTNWeightQuantConfig, quantize

        global_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="nf4")
        # set operator instance
        fc1_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="int8", white_list=["model.fc1"])
        # get model and quantize
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config=global_config + fc1_config)
        self.assertIsNotNone(qmodel)

    def test_config_white_lst2(self):
        from neural_compressor.torch import RTNWeightQuantConfig
        from neural_compressor.torch.utils import get_model_info

        global_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="nf4")
        # set operator instance
        fc1_config = RTNWeightQuantConfig(weight_bits=6, weight_dtype="int8", white_list=["fc1"])
        quant_config = global_config + fc1_config
        # get model and quantize
        fp32_model = build_simple_torch_model()
        model_info = get_model_info(fp32_model, white_module_list=[torch.nn.Linear])
        logger.info(quant_config)
        configs_mapping = quant_config.to_config_mapping(model_info=model_info)
        logger.info(configs_mapping)
        self.assertTrue(configs_mapping[(torch.nn.Linear, "fc1")].weight_bits == 6)
        self.assertTrue(configs_mapping[(torch.nn.Linear, "fc2")].weight_bits == 4)

    def test_config_from_dict(self):
        from neural_compressor.torch import RTNWeightQuantConfig

        quant_config = {
            "rtn_weight_only_quant": {
                "global": {
                    "weight_dtype": "nf4",
                    "weight_bits": 4,
                    "weight_group_size": 32,
                },
                "local": {
                    "fc1": {
                        "weight_dtype": "int8",
                        "weight_bits": 4,
                    }
                },
            }
        }
        config = RTNWeightQuantConfig.from_dict(quant_config["rtn_weight_only_quant"])
        self.assertIsNotNone(config.local_config)

    def test_config_to_dict(self):
        from neural_compressor.torch import RTNWeightQuantConfig

        quant_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="nf4")
        fc1_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="int8")
        quant_config.set_local("model.fc1", fc1_config)
        config_dict = quant_config.to_dict()
        self.assertIn("global", config_dict)
        self.assertIn("local", config_dict)

    def test_same_type_configs_addition(self):
        from neural_compressor.torch import RTNWeightQuantConfig

        quant_config1 = {
            "rtn_weight_only_quant": {
                "weight_dtype": "nf4",
                "weight_bits": 4,
                "weight_group_size": 32,
            },
        }
        q_config = RTNWeightQuantConfig.from_dict(quant_config1["rtn_weight_only_quant"])
        quant_config2 = {
            "rtn_weight_only_quant": {
                "global": {
                    "weight_bits": 8,
                    "weight_group_size": 32,
                },
                "local": {
                    "fc1": {
                        "weight_dtype": "int8",
                        "weight_bits": 4,
                    }
                },
            }
        }
        q_config2 = RTNWeightQuantConfig.from_dict(quant_config2["rtn_weight_only_quant"])
        q_config3 = q_config + q_config2
        q3_dict = q_config3.to_dict()
        for op_name, op_config in quant_config2["rtn_weight_only_quant"]["local"].items():
            for attr, val in op_config.items():
                self.assertEqual(q3_dict["local"][op_name][attr], val)
        self.assertNotEqual(
            q3_dict["global"]["weight_bits"], quant_config2["rtn_weight_only_quant"]["global"]["weight_bits"]
        )

    def test_diff_types_configs_addition(self):
        from neural_compressor.torch import GPTQConfig, RTNWeightQuantConfig

        quant_config1 = {
            "rtn_weight_only_quant": {
                "weight_dtype": "nf4",
                "weight_bits": 4,
                "weight_group_size": 32,
            },
        }
        q_config = RTNWeightQuantConfig.from_dict(quant_config1["rtn_weight_only_quant"])
        d_config = GPTQConfig(double_quant_bits=4)
        combined_config = q_config + d_config
        combined_config_d = combined_config.to_dict()
        logger.info(combined_config)
        self.assertTrue("rtn_weight_only_quant" in combined_config_d)
        self.assertIn("gptq", combined_config_d)

    def test_composable_config_addition(self):
        from neural_compressor.torch import GPTQConfig, RTNWeightQuantConfig

        quant_config1 = {
            "rtn_weight_only_quant": {
                "weight_dtype": "nf4",
                "weight_bits": 4,
                "weight_group_size": 32,
            },
        }
        q_config = RTNWeightQuantConfig.from_dict(quant_config1["rtn_weight_only_quant"])
        d_config = GPTQConfig(double_quant_bits=4)
        combined_config = q_config + d_config
        combined_config_d = combined_config.to_dict()
        logger.info(combined_config)
        self.assertTrue("rtn_weight_only_quant" in combined_config_d)
        self.assertIn("gptq", combined_config_d)
        combined_config2 = combined_config + d_config
        combined_config3 = combined_config + combined_config2

    def test_config_mapping(self):
        from neural_compressor.torch import RTNWeightQuantConfig
        from neural_compressor.torch.utils import get_model_info

        quant_config = RTNWeightQuantConfig(weight_bits=4, weight_dtype="nf4")
        # set operator instance
        fc1_config = RTNWeightQuantConfig(weight_bits=6, weight_dtype="int8")
        quant_config.set_local("fc1", fc1_config)
        # get model and quantize
        fp32_model = build_simple_torch_model()
        model_info = get_model_info(fp32_model, white_module_list=[torch.nn.Linear])
        logger.info(quant_config)
        configs_mapping = quant_config.to_config_mapping(model_info=model_info)
        logger.info(configs_mapping)
        self.assertTrue(configs_mapping[(torch.nn.Linear, "fc1")].weight_bits == 6)
        self.assertTrue(configs_mapping[(torch.nn.Linear, "fc2")].weight_bits == 4)

    def test_gptq_config(self):
        from neural_compressor.torch.quantization import GPTQConfig

        gptq_config1 = GPTQConfig(weight_bits=8, pad_max_length=512)
        quant_config_dict = {
            "gptq": {"weight_bits": 8, "pad_max_length": 512},
        }
        gptq_config2 = GPTQConfig.from_dict(quant_config_dict["gptq"])
        self.assertEqual(gptq_config1.to_dict(), gptq_config2.to_dict())


if __name__ == "__main__":
    unittest.main()
