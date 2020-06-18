import os
import argparse

import utils

TRIAL_CONFIG_FORMATS = {
    'widths_num_tiles': ["solver_config/widths_num_tiles/config-%s-50_num_tiles.json",
                         "solver_config/widths_num_tiles/config-%s-100_num_tiles.json",
                         "solver_config/widths_num_tiles/config-%s-150_num_tiles.json"],
    'controllability': ["solver_config/controllability/config-%s-100_bonus_a.json",
                        "solver_config/controllability/config-%s-100_bonus_b.json",
                        "solver_config/controllability/config-%s-100_bonus_c.json",
                        "solver_config/controllability/config-%s-100_hazard_a.json",
                        "solver_config/controllability/config-%s-100_hazard_b.json",
                        "solver_config/controllability/config-%s-100_hazard_c.json",
                        "solver_config/controllability/config-%s-100_block_a.json",
                        "solver_config/controllability/config-%s-100_block_b.json",
                        "solver_config/controllability/config-%s-100_block_c.json"]
}


def main(game, levels, process, solve, trial, max_sol, threads):

    if process:
        print("----- PROCESSING -----")
        process_dir = utils.get_directory("process_console_output")

        for level in levels:
            process_file = utils.get_filepath(process_dir, "%s.txt" % level)
            os.system("(time pypy3 main.py platformer %s %s --process) > %s 2>&1" % (game, level, process_file))
            os.system("(time python main.py platformer %s %s --gen_prolog) >> %s 2>&1" % (game, level, process_file))
            print("Saved to: %s" % process_file)

    if solve:
        print("----- SOLVING -----")
        config_formats = TRIAL_CONFIG_FORMATS.get(trial)
        if config_formats is None:
            utils.error_exit("--trial must be one of %s" % str(list(TRIAL_CONFIG_FORMATS.keys())))

        prolog_file_format = "level_saved_files_block/prolog_files/%s.pl"
        level_structural_txt_file_format = "level_structural_layers/generated/%s.txt"
        level_model_str_file_format = "level_saved_files_block/generated_level_model_strs/%s.txt"
        level_assignments_dict_file_format = "level_saved_files_block/generated_level_assignments_dicts/%s.pickle"
        level_valid_path_file_format = "level_saved_files_block/generated_level_paths/%s.pickle"
        level_state_graph_file_format = "level_saved_files_block/enumerated_state_graphs/generated/%s.gpickle"

        solve_dir = utils.get_directory("solver_console_output")
        sol_order = list(range(max_sol))
        sol_order.reverse()

        for sol in sol_order:
            for config_file_format in config_formats:
                for level in levels:
                    prolog_file = prolog_file_format % level
                    prolog_filename = utils.get_basepath_filename(prolog_file, 'pl')
                    config_file = config_file_format % level
                    config_filename = utils.get_basepath_filename(config_file, 'json')

                    answer_set_filename_format = '_'.join([prolog_filename, config_filename, 'a%d'])
                    cur_answer_set_filename = answer_set_filename_format % sol
                    default_answer_set_filename = answer_set_filename_format % 0

                    solve_file = utils.get_filepath("%s/%s/" % (solve_dir, level),
                                                    "%s.txt" % cur_answer_set_filename)

                    os.system("(time python run_solver.py %s %s --max_sol 1 --threads %d --save --validate) > %s 2>&1" % (
                        prolog_file, config_file, threads, solve_file
                    ))
                    print("Saved to: %s" % solve_file)

                    if sol != 0 and os.path.exists(level_structural_txt_file_format % default_answer_set_filename):
                        os.system("mv %s %s" % (level_structural_txt_file_format % default_answer_set_filename,
                                                level_structural_txt_file_format % cur_answer_set_filename))

                    if sol != 0 and os.path.exists(level_assignments_dict_file_format % default_answer_set_filename):
                        os.system("mv %s %s" % (level_assignments_dict_file_format % default_answer_set_filename,
                                                level_assignments_dict_file_format % cur_answer_set_filename))

                    if sol != 0 and os.path.exists(level_model_str_file_format % default_answer_set_filename):
                        os.system("mv %s %s" % (level_model_str_file_format % default_answer_set_filename,
                                                level_model_str_file_format % cur_answer_set_filename))

                    if sol != 0 and os.path.exists(level_valid_path_file_format % default_answer_set_filename):
                        os.system("mv %s %s" % (level_valid_path_file_format % default_answer_set_filename,
                                                level_valid_path_file_format % cur_answer_set_filename))

                    if sol != 0 and os.path.exists(level_state_graph_file_format % default_answer_set_filename):
                        os.system("mv %s %s" % (level_state_graph_file_format % default_answer_set_filename,
                                                level_state_graph_file_format % cur_answer_set_filename))

                    if os.path.exists(level_structural_txt_file_format % cur_answer_set_filename):
                        print("Level txt path: %s" % level_structural_txt_file_format % cur_answer_set_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Make system calls to process and run solver for specified levels')
    parser.add_argument('game', type=str, help="Game name")
    parser.add_argument('levels', type=str, nargs='+', help="Level names")
    parser.add_argument('--process', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--solve', const=True, nargs='?', type=bool, default=False)
    parser.add_argument('--trial', type=str, help="Trial to run: options = %s" % str(list(TRIAL_CONFIG_FORMATS.keys())))
    parser.add_argument('--max_sol', type=int, default=1, help="Max number of answer sets to return per solver config")
    parser.add_argument('--threads', type=int, default=1, help="Number of threads to run the solver on")
    args = parser.parse_args()
    main(game=args.game, levels=args.levels, process=args.process, solve=args.solve, trial=args.trial,
         max_sol=args.max_sol, threads=args.threads)

