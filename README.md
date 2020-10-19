# platformer

Help this hungry turtle cross the city and collect pizza with his awesome ninja jumping skills. Cowabunga! 

Generate new levels from existing examples to extend the adventure.

Hot keys:
- **Arrow Keys** or **WASD** to move the turtle
- **q** to quit game
- **r** to reset level

Genre: Basic Platform Game  
Pygame, Python, Clingo

### I. Setting up the repository
- Clone the git repo on your local machine

- Install miniconda (https://docs.conda.io/en/latest/miniconda.html)

- Run "conda update conda"

- Run "conda create -n platformer python=3.7"

- Run "conda activate platformer"

- Run "conda install -c potassco clingo scikit-learn"

- Run "python3 -m pip install -U pygame"


### II. Playing the game

Run "python main.py **environment** **game** **level**"

Run "pythohn main.py --help" for a full list of options available (includes drawing metatile labels and solution paths)


### III. Processing a new level
- Save level structural txt file in "level_structural_layers/**game**/**level**.txt" (see txt file format in [TheVGLC](https://github.com/TheVGLC/TheVGLC) for examples)  
  
- Run "pypy3 main.py **environment** **game** **level** --process"
- Run "python main.py **environment** **game** **level** --gen_prolog"

 
### IV: Running the solver to generate new levels

- Create a config JSON file to specify design decisions (e.g. level_w, level_h, etc). See config_template.json for an example.

- Run clingo solver
  - Run "python run_solver.py **prolog_filepath** **config_filepath** --max_sol **num_levels_to_generate** 
  --threads **num_threads_to_use**"
  - Add "--save" to save generated levels
  - Add "--print_level" to print the txt structure of generated levels to the console
  - Add "--validate" to validate the generated level (ensure playability and reachability constraints are met)
  - Run "python run_solver.py --help" for a full list of options available

### V. Putting It All Together with an Example (single training level)

Steps to generate 5 NxM sized levels from the level "example_level" in a platformer game "example_game"  

1. Run the commands in Step I (setting up the repository)  
2. Save the level structural layer in the path: "level_structural_layers/example_game/example_level.txt"  
3. Run "pypy3 main.py platformer example_game example_level --process"  
4. Run "python main.py platformer example_game example_level --gen_prolog"
5. Make a copy of *config_basic_template.json* and save it as *config_example_level.json*
6. Open *config_example_level.json* in a text editor and set width and height to N and M, respectively. Save and close the file.
7. Run "python run_solver.py level_saved_files_block/prolog_files/example_level.pl config_example_level.json --max_sol 5 --print_level --save --validate"

Generated levels are stored in the directory: "level_structural_layers/generated".  

To play the first generated level run "python main.py platformer generated example_level_config_example_level_a0"

### Saved filepaths
- metatile constraints files: "level_saved_files_block/metatile_constraints/"

- prolog files: "level_saved_files_block/prolog_files/"

- level structural txt files: "level_structural_layers/**game**/**level**.txt"
