#!/bin/bash
# set -x

function main {

  init_params "$@"

  run_tuning

}

# init params
function init_params {
  # set default value
  input_model="./distilbert_base_fp32.pb"
  dataset_location="./sst2_validation_dataset"
  output_model="./output_distilbert_base_int8.pb"
  config="./distilbert_base.yaml"
  batch_size=128
  max_seq_length=128
  warmup_steps=10
  num_inter=2
  num_intra=28

  for var in "$@"
  do
    case $var in
      --topology=*)
          topology=$(echo $var |cut -f2 -d=)
      ;;
      --input_model=*)
          input_model=$(echo ${var} |cut -f2 -d=)
      ;;
      --dataset_location=*)
          dataset_location=$(echo ${var} |cut -f2 -d=)
      ;;
      --output_model=*)
          output_model=$(echo ${var} |cut -f2 -d=)
      ;;
      --config=*)
          config=$(echo ${var} |cut -f2 -d=)
      ;;
      --batch_size=*)
          batch_size=$(echo ${var} |cut -f2 -d=)
      ;;
      --max_seq_length=*)
          max_seq_length=$(echo ${var} |cut -f2 -d=)
      ;;
      --warmup_steps=*)
          warmup_steps=$(echo ${var} |cut -f2 -d=)
      ;;
      --num_inter=*)
         num_inter=$(echo ${var} |cut -f2 -d=)
      ;;
      --num_intra=*)
         num_intra=$(echo ${var} |cut -f2 -d=)
      ;;
      *)
          echo "Parameter error: ${var}"
          exit 1
      ;;
    esac
  done

}

# run_tuning
function run_tuning {
    cmd="
        python run_inference.py \
            --in-graph=${input_model} \
            --data-location=${dataset_location} \
            --output-graph=${output_model} \
            --config=${config} \
            --mode=tune \
            --warmup-steps=${warmup_steps} \
            --batch-size=${batch_size} \
            --max-seq-length=${max_seq_length} \
            --num-inter-threads=${num_inter} \
            --num-intra-threads=${num_intra}
        "
    echo $cmd
    eval $cmd
}

main "$@"
