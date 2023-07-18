"""retrain free pruner."""
# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Intel Corporation
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

from .base import (register_pruner,
                   PytorchBasePruner)
from ..schedulers import get_scheduler
from ..patterns import get_pattern
from ..criteria import get_criterion
from ..regs import get_reg
from ..utils import logger

from ..utils import torch

@register_pruner('pt_retrain_free')
class PytorchRetrainFreePruner(PytorchBasePruner):
    """Pruning Pruner.
    The retrain_free pruner_class is derived from BasePruner.
    This pruner references the mask search and mask rearrangement strategies in fast retraining free.
    RetrainFreePruner supports one-shot pruning (same effect as fast retraining free) and iterative pruning.
    Please refer to A Fast Post-Training Pruning Framework for Transformers
        (https://arxiv.org/abs/2204.09656)

    1. Defines pruning functions called at step begin/end, before/after optimize and epoch begin/end.
    2. Defines the pruning criterion and fixed weight parameters.
    3. Obtain block masks and its grads.
    4. Rearrange block masks.

    Args:
        modules: A dict {"module_name": Tensor} that stores the pruning modules' weights.
        config: A config dict object that contains the pruner information.

    Attributes:
        pattern: A Pattern object that defines pruning weights' arrangements within space.
        criterion: A Criterion Object that defines which weights are to be pruned
        scheduler: A Scheduler object that defines how the model's sparsity changes as training/pruning proceeds.
        reg: A Reg object that defines regulization terms.
    """

    def __init__(self, config, modules):
        """Initialize."""
        super().__init__(config, modules)

    def _init(self):
        """Initialize."""
        self.pattern = get_pattern(self.config, self.modules)
        self.masks = self.pattern.register_block_masks(self.modules)
        self.rewrite_forward()
        self.scheduler = get_scheduler(self.config)
        self.criterion = get_criterion(self.config, self.modules, self.pattern)
        self.reg = get_reg(self.config, self.modules, self.pattern)

        logger.warning("Retrain-free pruner fixed the weights, please DO NOT turn on gradient update.")
        assert "channel" in self.pattern.pattern, \
            "retrain-free pruner only supports large patterns like channel-wise pruning."

    # def on_step_begin(self, local_step):
    #     """Implement at the start of each step.

    #     Update the masks at a given local_step.
    #     """
    #     self.update_masks(local_step)

    def update_masks(self, local_step):
        """Update the masks at a given local step."""
        if self.global_step == self.start_step:
            if self.config['lock_init_sparsity']:
                self.init_sparsity_ratio = self.pattern.get_sparsity_ratio(self.masks)
                self.current_sparsity_ratio = self.init_sparsity_ratio

        if not self.check_is_pruned_step(self.global_step):
            return

        if self.current_sparsity_ratio > self.target_sparsity_ratio:
            return

        self.criterion.on_step_begin()
        current_target_sparsity_ratio = self.scheduler.update_sparsity_ratio(self.target_sparsity_ratio,
                                                                             self.completed_pruned_cnt,
                                                                             self.total_prune_cnt, self.masks,
                                                                             self.init_sparsity_ratio)
        logger.info(f"current target ratio is {current_target_sparsity_ratio}")

        self.completed_pruned_cnt += 1
        if self.criterion.scores == {}:
            return
        # the order of the following three lines can't not be exchanged
        self.masks = self.pattern.get_masks(self.criterion.scores, current_target_sparsity_ratio, self.masks)
        self.rearrange_masks(self.masks)
        self.update_block_masks(self.masks)

        self.current_sparsity_ratio = self.pattern.get_sparsity_ratio(self.masks)
        logger.info(f"current sparsity ratio is {self.current_sparsity_ratio}")

    def on_before_optimizer_step(self):
        """Implement before optimizer.step()."""
        if self.global_step >= self.start_step and self.global_step <= self.end_step:
            self.reg.on_before_optimizer_step()
            self.criterion.on_before_optimizer_step()

    def on_after_optimizer_step(self):
        """Prune the model after optimization."""
        # the order of the following four lines can't not be exchanged
        if self.global_step >= self.start_step and self.global_step <= self.end_step:
            self.reg.on_after_optimizer_step()
        # self.mask_weights()
        # Iterative rearrangement with mask weight at the last step only
        if self.end_step == self.global_step:
            self.mask_weights()
            logger.info(f"mask weights at last_prune_step: {self.global_step}")
            # recover forward method and remove block mask parameters at last prune step
            self.recover_forward()
            self.pattern.remove_block_masks()
        self.global_step += 1

    def mask_weights(self):
        """Apply block masks to corresponding modules' weights.

        Weights are multipled with masks. This is the formal pruning process.
        """
        with torch.no_grad():
            self.pattern.mask_block_weights(self.masks)

    def update_block_masks(self, masks):
        """Update the block mask parameters."""
        with torch.no_grad():
            for key in self.masks.keys():
                module = self.modules[key]
                module.block_mask.data = masks[key].float().data

    def rearrange_masks(self, masks):
        """Rearrange the masks of each layer with constant sparsity."""
        with torch.no_grad():
            new_masks = {}
            for key in masks.keys():
                block_mask = masks[key]
                num_pruned = torch.sum(block_mask == 0.0).data.item()
                if not num_pruned or not self.criterion.collected_grads[key]:
                    new_masks[key] = block_mask
                    continue
                grads = torch.stack(self.criterion.collected_grads[key], dim=0).squeeze()
                grads = grads.permute(1, 0).contiguous()
                grads_sq = grads.pow(2).sum(dim=1)
                _, indicies = grads_sq.sort(descending=False)
                indicies = indicies.tolist()
                masked_indicies = indicies[:num_pruned]
                for index in indicies[num_pruned:]:
                    masked_indicies.append(index)
                    grad_vectors = grads[masked_indicies]
                    grad_sum = grad_vectors.sum(dim=0)
                    complement = grad_sum - grad_vectors
                    grad_sum_length = complement.pow(2).sum(dim=1)
                    removed = grad_sum_length.argmin()
                    del masked_indicies[removed]

                new_masks[key] = torch.ones(len(indicies)).to(block_mask.device)
                new_masks[key][masked_indicies] = 0
                new_masks[key] = new_masks[key] * torch.ones_like(block_mask).to(block_mask.device)
            self.masks = new_masks

    def zero_mask_grad(self):
        with torch.no_grad():
            for key in self.modules.keys():
                if not hasattr(self.modules[key], 'block_mask'):
                    continue  # No corresponding block mask, skip.
                mask = self.modules[key].block_mask
                if mask.grad is not None:
                    if mask.grad.grad_fn is not None:
                        mask.grad.detach_()
                    else:
                        mask.grad.requires_grad_(False)
                    mask.grad.zero_()
