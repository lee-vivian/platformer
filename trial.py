import os

# levels = ['mario-sample-gaps-border']
levels = ["mario-1-1", "mario-1-2", "mario-1-3"]

# ----- PROCESS -----
for level in levels:
    print("Processing Level: %s" % level)
    os.system("(time pypy3 main.py platformer super_mario_bros %s --process) > process-%s.txt 2>&1" % (level, level))
    print("Saved to: process-%s.txt" % level)

# ----- SOLVE -----
solver_widths = [50, 100, 150]
max_sol = 2
threads = 12

for level in levels:
    prolog_file = "level_saved_files_block/prolog_files/%s.pl" % level
    for w in solver_widths:
        config_file_prefix = "config-%s-%d" % (level, w)
        config_file = "solver_config/%s.json" % config_file_prefix
        os.system("(time python run_solver.py %s %s --max_sol %d --threads %d --save --validate) > %s-%s.txt 2>&1" % (
            prolog_file, config_file, max_sol, threads, level, config_file_prefix))
        print("Saved to: %s-%d.txt" % (level, w))
