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

import os
import subprocess
import sys

from argparse import ArgumentParser, REMAINDER

def parse_args():
    """
    Helper function parsing the command line options
    @retval ArgumentParser
    """
    parser = ArgumentParser(description="command-launch a Python script with quantization auto-enabled")

    parser.add_argument("-o", "--opt", type=str, default="",
                        help="optimization feature to enable")

    parser.add_argument("-a", "--approach", type=str, default="static",

                        help="quantization approach (strategy)")

    parser.add_argument('--config', type=str, default="",
                        help='quantization configuration file path')

    # positional
    parser.add_argument("script", type=str,
                        help="The full path to the script to be launched. "
                             "followed by all the arguments for the script")

    # script args
    parser.add_argument('script_args', nargs=REMAINDER)
    return parser.parse_args()

args = parse_args()

# copy user entry script (main.py -> main_optimized.py)
import shutil
script_copied = args.script[:-3] + "_optimized.py"
shutil.copy(args.script, script_copied)

# optimize on copied script with Neural Coder
from neural_coder import enable
if args.opt == "":
    if args.approach == "static":
        features = ["pytorch_inc_static_quant_fx"]
    if args.approach == "static_ipex":
        features = ["pytorch_inc_static_quant_ipex"]
    if args.approach == "dynamic":
        features = ["pytorch_inc_dynamic_quant"]
else:
    features = args.opt.split(",")

# execute optimization enabling
enable(
    code=script_copied,
    features=features,
    overwrite=True,
)

# execute on copied script, which has already been optimized
cmd = []

cmd.append(sys.executable) # "/xxx/xxx/python"
cmd.append("-u")
cmd.append(script_copied)
cmd.extend(args.script_args)

cmd = " ".join(cmd) # list convert to string

process = subprocess.Popen(cmd, env=os.environ, shell=True)  # nosec
process.wait()
