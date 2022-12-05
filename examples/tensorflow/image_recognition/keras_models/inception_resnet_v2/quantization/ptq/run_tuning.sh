#!/bin/bash
set -x

function main {
  init_params "$@"
  run_tuning

}

# init params
function init_params {

  for var in "$@"
  do
    case $var in
      --input_model=*)
          input_model=$(echo $var |cut -f2 -d=)
      ;;
      --output_model=*)
          output_model=$(echo $var |cut -f2 -d=)
      ;;
      --eval_data=*)
          eval_data=$(echo $var |cut -f2 -d=)
      ;;
      --calib_data=*)
          calib_data=$(echo $var |cut -f2 -d=)
      ;;
    esac
  done

}

# run_tuning
function run_tuning {
    python main.py \
            --input_model ${input_model} \
            --output_model ${output_model} \
            --eval_data ${eval_data} \
            --calib_data ${calib_data} \
            --tune
}

main "$@"
