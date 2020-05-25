import os

levels = ["mario-1-1", "mario-1-2", "mario-1-3"]

# ----- PROCESS -----
for level in levels:
    os.system("pypy3 main.py platformer super_mario_bros %s --process" % level)

# ----- SOLVE -----
solver_widths = [50, 100, 150]
max_sol = 2
threads = 12

for level in levels:
    prolog_file = "level_saved_files_block/prolog_files/%s.pl" % level
    for w in solver_widths:
        config_file = "config-%s-%d.json" % (level, w)
        os.system("time python run_solver.py %s %s --max_sol %d --threads %d --save --validate > %s-%d.txt" % (
            prolog_file, config_file, max_sol, threads, level, w))
        print("Saved to: %s-%d.txt" % (level, w))
