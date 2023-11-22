python examples/pytorch/nlp/huggingface_models/language-modeling/quantization/ptq_weight_only/run-gptq-llm.py \
    --model_name_or_path facebook/opt-125m \
    --weight_only_algo GPTQ \
    --dataset NeelNanda/pile-10k \
    --wbits 4 \
    --group_size 128 \
    --pad_max_length 2048 \
    --use_max_length \
    --seed 0 \
    --gpu
