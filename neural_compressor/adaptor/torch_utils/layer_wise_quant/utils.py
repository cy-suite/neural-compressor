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
"""Utils for layer wise quantization."""

import os
import json

from neural_compressor.utils.utility import LazyImport
torch = LazyImport("torch")
from accelerate import init_empty_weights
from transformers import AutoConfig
from transformers.models.auto.auto_factory import _BaseAutoModelClass

from .torch_load import load


def get_children(model):
    """Get all the children of given model."""
    module_list = []
    children = list(model.children())
    if len(children) == 0:
        return [model]
    for child in children:
        module_list += get_children(child)
    return module_list


def get_named_children(model, pre=[]):
    """Get all the name and children of given model."""
    module_list = []
    if len(list(model.children())) == 0:
        return [('.'.join(pre), model)]
    for name, module in model.named_children():
        module_list += get_named_children(module, pre=pre + [name])
    return module_list


def dowload_hf_model(repo_id, cache_dir=None, repo_type=None, revision=None):
    """Download hugging face model from hf hub."""
    from huggingface_hub.file_download import repo_folder_name, REGEX_COMMIT_HASH
    from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE, DEFAULT_REVISION
    from huggingface_hub.utils import EntryNotFoundError
    if cache_dir is None:
        cache_dir = HUGGINGFACE_HUB_CACHE
    if revision is None:
        revision = DEFAULT_REVISION
    if repo_type is None:
        repo_type = 'model'
    storage_folder = os.path.join(
        cache_dir, repo_folder_name(repo_id=repo_id, repo_type=repo_type)
    )
    commit_hash = None
    if REGEX_COMMIT_HASH.match(revision):
        commit_hash = revision
    else:
        ref_path = os.path.join(storage_folder, "refs", revision)
        if os.path.exists(ref_path):
            with open(ref_path) as f:
                commit_hash = f.read()
    pointer_path = os.path.join(
        storage_folder, "snapshots", commit_hash
    )
    if os.path.isdir(pointer_path):
        return pointer_path
    else:  # pragma: no cover
        from huggingface_hub import snapshot_download
        file_path = snapshot_download(repo_id)
        return file_path


def load_shell(pretrained_model_name_or_path, cls):
    """Load a empty model."""
    is_local = os.path.isdir(pretrained_model_name_or_path)
    if is_local:  # pragma: no cover
        path = pretrained_model_name_or_path
    else:
        path = dowload_hf_model(pretrained_model_name_or_path)
    if cls.__base__ == _BaseAutoModelClass:
        config = AutoConfig.from_pretrained(path)
        with init_empty_weights():
            model = cls.from_config(config)
    else:  # pragma: no cover
        config = cls.config_class.from_pretrained(path)
        with init_empty_weights():
            model = cls(config)
    model.tie_weights()
    model.eval()
    return model


def get_super_module_by_name(model, module_name):
    """Get the father module with given name of child module."""
    name_list = module_name.split(".")
    for name in name_list[:-1]:
        if hasattr(model, name):
            model = getattr(model, name)
        else:  # pragma: no cover
            return None
    if hasattr(model, name_list[-1]):
        return model
    else:  # pragma: no cover
        return None


def update_module(model, module_name, new_module):
    """Update module."""
    super_module = get_super_module_by_name(model, module_name)
    if super_module:
        setattr(super_module, module_name.split('.')[-1], new_module)


def load_layer_wise_quantized_model(path):  # pragma: no cover
    """Load layer wise quantized model."""
    model = torch.load(os.path.join(path, 'model_arch.pt'))
    for name, _ in model.named_modules():
        if name + '.pt' in os.listdir(path):
            update_module(model, name, torch.load(os.path.join(path, name + '.pt')))
    model.eval()
    return model


def load_tensor_from_shard(pretrained_model_name_or_path,
                           tensor_name,
                           prefix=None):  # pragma: no cover
    """Load tensor from shard."""
    path = _get_path(pretrained_model_name_or_path)
    idx_dict = json.load(open(os.path.join(path, 'pytorch_model.bin.index.json'), 'r'))['weight_map']
    if tensor_name not in idx_dict.keys():
        if tensor_name.replace(f'{prefix}.', '') in idx_dict.keys():
            tensor_name = tensor_name.replace(f'{prefix}.', '')
        else:
            assert False, '{} not in the index.json'.format(tensor_name)
    return load_tensor(os.path.join(path, idx_dict[tensor_name]), tensor_name, None)


def load_tensor(path, tensor_name=None, prefix=None):
    """Load a tensor from bin file with given tensor name."""
    # transformers.modeling_utils
    if tensor_name:
        if "gamma" in tensor_name:  # pragma: no cover
            tensor_name = tensor_name.replace("gamma", "weight")
        if "beta" in tensor_name:  # pragma: no cover
            tensor_name = tensor_name.replace("beta", "bias")

    if os.path.isdir(path):
        path = os.path.join(path, 'pytorch_model.bin')
    state_dict = load(path, tensor_name, prefix)
    if tensor_name:
        if tensor_name in state_dict:
            return state_dict[tensor_name]
        else:  # pragma: no cover
            return state_dict[tensor_name.replace(f'{prefix}.', '')]
    else:  # pragma: no cover
        return state_dict

def _get_path(pretrained_model_name_or_path):
    is_local = os.path.isdir(pretrained_model_name_or_path)
    if is_local:  # pragma: no cover
        path = pretrained_model_name_or_path
    else:
        path = dowload_hf_model(pretrained_model_name_or_path)
    return path
