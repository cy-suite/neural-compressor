import copy
import unittest

import torch
import transformers

from neural_compressor.torch.quantization import (
    GPTQConfig,
    RTNConfig,
    SmoothQuantConfig,
    StaticQuantConfig,
    get_default_rtn_config,
    quantize,
)
from neural_compressor.torch.utils import get_model_info, logger


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

        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config=get_default_rtn_config())
        self.assertIsNotNone(qmodel)

    def test_quantize_rtn_from_dict_beginner(self):
        quant_config = {
            "rtn": {
                "dtype": "nf4",
                "bits": 4,
                "group_size": 32,
            },
        }
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_quantize_rtn_from_class_beginner(self):
        quant_config = RTNConfig(bits=4, dtype="nf4", group_size=32)
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_quantize_rtndq_from_class_beginner(self):
        fp32_config = RTNConfig(dtype="fp32")

        fp32_model = copy.deepcopy(self.gptj)
        quant_config = RTNConfig(
            bits=4,
            dtype="int",
            use_sym=False,
            group_size=32,
        )
        quant_config.set_local("lm_head", fp32_config)
        qmodel = quantize(fp32_model, quant_config)
        out2 = qmodel(self.lm_input)

        fp32_model = copy.deepcopy(self.gptj)

    def test_quantize_rtn_from_dict_advance(self):
        fp32_model = build_simple_torch_model()
        quant_config = {
            "rtn": {
                "global": {
                    "dtype": "nf4",
                    "bits": 4,
                    "group_size": 32,
                },
                "local": {
                    "fc1": {
                        "dtype": "int8",
                        "bits": 4,
                    }
                },
            }
        }
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_quantize_rtn_from_class_advance(self):
        quant_config = RTNConfig(bits=4, dtype="nf4")
        # set operator instance
        fc1_config = RTNConfig(bits=4, dtype="int8")
        quant_config.set_local("model.fc1", fc1_config)
        # get model and quantize
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config)
        self.assertIsNotNone(qmodel)

    def test_config_white_lst(self):
        global_config = RTNConfig(bits=4, dtype="nf4")
        # set operator instance
        fc1_config = RTNConfig(bits=4, dtype="int8", white_list=["model.fc1"])
        # get model and quantize
        fp32_model = build_simple_torch_model()
        qmodel = quantize(fp32_model, quant_config=global_config + fc1_config)
        self.assertIsNotNone(qmodel)

    def test_config_white_lst2(self):
        global_config = RTNConfig(bits=4, dtype="nf4")
        # set operator instance
        fc1_config = RTNConfig(bits=6, dtype="int8", white_list=["fc1"])
        quant_config = global_config + fc1_config
        # get model and quantize
        fp32_model = build_simple_torch_model()
        model_info = get_model_info(fp32_model, white_module_list=[torch.nn.Linear])
        logger.info(quant_config)
        configs_mapping = quant_config.to_config_mapping(model_info=model_info)
        logger.info(configs_mapping)
        self.assertTrue(configs_mapping[("fc1", torch.nn.Linear)].bits == 6)
        self.assertTrue(configs_mapping[("fc2", torch.nn.Linear)].bits == 4)

    def test_config_from_dict(self):
        quant_config = {
            "rtn": {
                "global": {
                    "dtype": "nf4",
                    "bits": 4,
                    "group_size": 32,
                },
                "local": {
                    "fc1": {
                        "dtype": "int8",
                        "bits": 4,
                    }
                },
            }
        }
        config = RTNConfig.from_dict(quant_config["rtn"])
        self.assertIsNotNone(config.local_config)

    def test_config_to_dict(self):
        quant_config = RTNConfig(bits=4, dtype="nf4")
        fc1_config = RTNConfig(bits=4, dtype="int8")
        quant_config.set_local("model.fc1", fc1_config)
        config_dict = quant_config.to_dict()
        self.assertIn("global", config_dict)
        self.assertIn("local", config_dict)

    def test_same_type_configs_addition(self):
        quant_config1 = {
            "rtn": {
                "dtype": "nf4",
                "bits": 4,
                "group_size": 32,
            },
        }
        q_config = RTNConfig.from_dict(quant_config1["rtn"])
        quant_config2 = {
            "rtn": {
                "global": {
                    "bits": 8,
                    "group_size": 32,
                },
                "local": {
                    "fc1": {
                        "dtype": "int8",
                        "bits": 4,
                    }
                },
            }
        }
        q_config2 = RTNConfig.from_dict(quant_config2["rtn"])
        q_config3 = q_config + q_config2
        q3_dict = q_config3.to_dict()
        for op_name, op_config in quant_config2["rtn"]["local"].items():
            for attr, val in op_config.items():
                self.assertEqual(q3_dict["local"][op_name][attr], val)
        self.assertNotEqual(q3_dict["global"]["bits"], quant_config2["rtn"]["global"]["bits"])

    def test_diff_types_configs_addition(self):
        quant_config1 = {
            "rtn": {
                "dtype": "nf4",
                "bits": 4,
                "group_size": 32,
            },
        }
        q_config = RTNConfig.from_dict(quant_config1["rtn"])
        d_config = GPTQConfig(double_quant_bits=4)
        combined_config = q_config + d_config
        combined_config_d = combined_config.to_dict()
        logger.info(combined_config)
        self.assertTrue("rtn" in combined_config_d)
        self.assertIn("gptq", combined_config_d)

    def test_composable_config_addition(self):
        quant_config1 = {
            "rtn": {
                "dtype": "nf4",
                "bits": 4,
                "group_size": 32,
            },
        }
        q_config = RTNConfig.from_dict(quant_config1["rtn"])
        d_config = GPTQConfig(double_quant_bits=4)
        combined_config = q_config + d_config
        combined_config_d = combined_config.to_dict()
        logger.info(combined_config)
        self.assertTrue("rtn" in combined_config_d)
        self.assertIn("gptq", combined_config_d)
        combined_config2 = combined_config + d_config
        combined_config3 = combined_config + combined_config2

    def test_config_mapping(self):
        quant_config = RTNConfig(bits=4, dtype="nf4")
        # set operator instance
        fc1_config = RTNConfig(bits=6, dtype="int8")
        quant_config.set_local("fc1", fc1_config)
        # get model and quantize
        fp32_model = build_simple_torch_model()
        model_info = get_model_info(fp32_model, white_module_list=[torch.nn.Linear])
        logger.info(quant_config)
        configs_mapping = quant_config.to_config_mapping(model_info=model_info)
        logger.info(configs_mapping)
        self.assertTrue(configs_mapping[("fc1", torch.nn.Linear)].bits == 6)
        self.assertTrue(configs_mapping[("fc2", torch.nn.Linear)].bits == 4)
        # test regular matching
        fc_config = RTNConfig(bits=5, dtype="int8")
        quant_config.set_local("fc", fc_config)
        configs_mapping = quant_config.to_config_mapping(model_info=model_info)
        logger.info(configs_mapping)
        self.assertTrue(configs_mapping[("fc1", torch.nn.Linear)].bits == 5)
        self.assertTrue(configs_mapping[("fc2", torch.nn.Linear)].bits == 5)
        self.assertTrue(configs_mapping[("fc3", torch.nn.Linear)].bits == 5)

    def test_gptq_config(self):
        gptq_config1 = GPTQConfig(weight_bits=8, pad_max_length=512)
        quant_config_dict = {
            "gptq": {"weight_bits": 8, "pad_max_length": 512},
        }
        gptq_config2 = GPTQConfig.from_dict(quant_config_dict["gptq"])
        self.assertEqual(gptq_config1.to_dict(), gptq_config2.to_dict())

    def test_static_quant_config(self):
        static_config1 = StaticQuantConfig(w_dtype="int8", act_sym=True, act_algo="minmax")
        quant_config_dict = {"static": {"w_dtype": "int8", "act_sym": True, "act_algo": "minmax"}}
        static_config2 = StaticQuantConfig.from_dict(quant_config_dict["static"])
        self.assertEqual(static_config1.to_dict(), static_config2.to_dict())

    def test_smooth_quant_config(self):
        sq_config1 = SmoothQuantConfig(alpha=0.8, folding=True)
        quant_config_dict = {"sq": {"alpha": 0.8, "folding": True}}
        sq_config2 = SmoothQuantConfig.from_dict(quant_config_dict["sq"])
        self.assertEqual(sq_config1.to_dict(), sq_config2.to_dict())


class TestQuantConfigForAutotune(unittest.TestCase):
    def test_expand_config(self):
        # test the expand functionalities, the user is not aware it

        tune_config = RTNConfig(bits=[4, 6])
        expand_config_list = RTNConfig.expand(tune_config)
        self.assertEqual(expand_config_list[0].bits, 4)
        self.assertEqual(expand_config_list[1].bits, 6)


if __name__ == "__main__":
    unittest.main()
