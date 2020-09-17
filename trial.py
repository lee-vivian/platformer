import os
import argparse
import subprocess

import utils

# PROLOG_FILE = "level_saved_files_block/prolog_files/mario-sample.pl"
# CONFIG_DIR = "solver_config/er_new/super_mario_bros/test"
# CONFIG_FILES = ["config-mario-sample-max-bon-max-haz.json",
#                 "config-mario-sample-max-haz-max-bon.json",
#                 "config-mario-sample-min-bon-min-haz.json",
#                 "config-mario-sample-min-haz-min-bon.json",
#                 "config-mario-sample-max-bon-min-haz.json",
#                 "config-mario-sample-min-haz-max-bon.json",
#                 "config-mario-sample-min-bon-max-haz.json",
#                 "config-mario-sample-max-haz-min-bon.json"]


# TRIAL_CONFIG_FORMATS = {
#     'widths_num_tiles': ["solver_config/widths_num_tiles/%s/config-%s-50_num_tiles.json",
#                          "solver_config/widths_num_tiles/%s/config-%s-100_num_tiles.json",
#                          "solver_config/widths_num_tiles/%s/config-%s-150_num_tiles.json"],
#     'controllability': ["solver_config/controllability/%s/config-%s-100_bonus_a.json",
#                         "solver_config/controllability/%s/config-%s-100_bonus_b.json",
#                         "solver_config/controllability/%s/config-%s-100_bonus_c.json",
#                         "solver_config/controllability/%s/config-%s-100_hazard_a.json",
#                         "solver_config/controllability/%s/config-%s-100_hazard_b.json",
#                         "solver_config/controllability/%s/config-%s-100_hazard_c.json",
#                         "solver_config/controllability/%s/config-%s-100_block_a.json",
#                         "solver_config/controllability/%s/config-%s-100_block_b.json",
#                         "solver_config/controllability/%s/config-%s-100_block_c.json"],
#     "er_new": [
#         "solver_config/er_new/%s/config-%s-max-blk-max-bon.json",
#         "solver_config/er_new/%s/config-%s-max-blk-max-haz.json",
#         "solver_config/er_new/%s/config-%s-max-blk-min-bon.json",
#         "solver_config/er_new/%s/config-%s-max-blk-min-haz.json",
#         "solver_config/er_new/%s/config-%s-max-bon-max-blk.json",
#         "solver_config/er_new/%s/config-%s-max-bon-max-haz.json",
#         "solver_config/er_new/%s/config-%s-max-bon-min-blk.json",
#         "solver_config/er_new/%s/config-%s-max-bon-min-haz.json",
#         "solver_config/er_new/%s/config-%s-max-haz-max-blk.json",
#         "solver_config/er_new/%s/config-%s-max-haz-max-bon.json",
#         "solver_config/er_new/%s/config-%s-max-haz-min-blk.json",
#         "solver_config/er_new/%s/config-%s-max-haz-min-bon.json",
#         "solver_config/er_new/%s/config-%s-min-blk-max-bon.json",
#         "solver_config/er_new/%s/config-%s-min-blk-max-haz.json",
#         "solver_config/er_new/%s/config-%s-min-blk-min-bon.json",
#         "solver_config/er_new/%s/config-%s-min-blk-min-haz.json",
#         "solver_config/er_new/%s/config-%s-min-bon-max-blk.json",
#         "solver_config/er_new/%s/config-%s-min-bon-max-haz.json",
#         "solver_config/er_new/%s/config-%s-min-bon-min-blk.json",
#         "solver_config/er_new/%s/config-%s-min-bon-min-haz.json",
#         "solver_config/er_new/%s/config-%s-min-haz-max-blk.json",
#         "solver_config/er_new/%s/config-%s-min-haz-max-bon.json",
#         "solver_config/er_new/%s/config-%s-min-haz-min-blk.json",
#         "solver_config/er_new/%s/config-%s-min-haz-min-bon.json"
#     ]
# }

def main(prolog_file, config_dir, max_time, threads, save):

    if not prolog_file.endswith(".pl"):
        utils.error_exit("prolog file must be a .pl file")

    files = os.listdir(config_dir)
    files.sort()

    for file in files:
        if not file.endswith(".json"):
            continue
        config_file = os.path.join(config_dir, file)

        print("----- Solving for [%s] -----" % config_file)
        try:
            cmd_args = ["python", "run_solver.py", prolog_file, config_file]
            cmd_args += ["--threads", threads] if threads > 1 else []
            cmd_args += ["--save"] if save else []
            subprocess.run(cmd_args, timeout=max_time)
        except subprocess.TimeoutExpired as e:
            print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Make system calls to run solver with specified constraint files')
    parser.add_argument('prolog_file', type=str, help="Filepath to prolog file")
    parser.add_argument('config_dir', type=str, help='Directory of config files to solve for')
    parser.add_argument('--max_time', type=int, default=1800, help='Max number of seconds allowed for each solver run')
    parser.add_argument('--threads', type=int, default=1, help='Number of threads to use for solving')
    parser.add_argument('--save', const=True, nargs='?', type=bool, default=False)
    args = parser.parse_args()

    main(args.prolog_file, args.config_dir, args.max_time, args.threads, args.save)

