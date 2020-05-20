# platformer

Help this hungry turtle cross the city and collect pizza with his awesome ninja jumping skills. Cowabunga! 

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

- Run "conda install -c potassco clingo"

- Run "python3 -m pip install -U pygame"


### II. Playing the game

Run "python3 main.py **environment** **game** **level**"

Run "python3 main.py --help" for a full list of options available (includes drawing metatile labels and solution paths)


### IIIa. Processing a new level individually (Creating metatile constraints file from a single level)
- Save level structural txt file in "level_structural_layers/**game**/**level**.txt" (see txt file format in [TheVGLC](https://github.com/TheVGLC/TheVGLC) for examples)  
  
- Run "python main.py **environment** **game** **level** --process"

### IIIb: Creating combined metatile constraints file from multiple levels  

- For each level you want to include do *one* of the following:  
    - Run "python main.py **environment** **game** **level** --process"
    - Run "python enumerate.py **game** **level** --player_img **player_img**"  
  Run "python extract_metatiles.py **level** --player_img **player_img** --state_graph_files level_saved_files_**player_img**/enumerated_state_graphs/**game**/**level**.gpickle"  
 
 
- Run "python combine_constraints.py game1/level1 game2/level2 etc. --save_filename **optional** --player_img **player_img**" 
 
### IV: Running the solver to generate new levels

- Create a config JSON file to specify design decisions (e.g. level_w, level_h, etc). See config_template.json for example.

- Run clingo solver
  - Run "python run_solver.py **prolog_filepath** **config_filepath** --max_sol **num_levels_to_generate** 
  --threads **num_threads_to_use**"
  - Add "--save" to save generated levels and/or "--print" to print the txt structure of generated levels to console
  - Run "python run_solver.py --help" for a full list of options available

### V. Putting It All Together with an Example (single training level)

Steps to generate 5 NxM sized levels from the level "example_level" in a platformer game "example_game"  

1. Run the commands in Step I (setting up the repository)  
2. Save the level structural layer in the path: "level_structural_layers/example_game/example_level.txt"  
3. Run "python main.py platformer example_game example_level --process"  
4. Make a copy of *config_basic_template.json* and save it as *config_example_level.json*
5. Open *config_example_level.json* and set width and height to N and M, respectively. Save and close the file.
6. Run "python run_solver.py level_saved_files_block/prolog_files/example_level.pl config_example_level.json --max_sol 5 --print_level --save"

Generated levels are stored in the directory: "level_structural_layers/generated".  

To play the first generated level run "python main.py platformer generated example_level_config_example_level_a0"


### VI. Putting It All Together with an Example (multiple training levels)

Steps to generate 5 levels from 2 sample levels: super_mario_bros/mario-sample-left and super_mario_bros/mario-sample-right

1. Run the commands in Step I (setting up the repository)
2. Run "python main.py platformer super_mario_bros mario-sample-left --process"
3. Run "python main.py platformer super_mario_bros mario-sample-right --process"
4. Run "python combine_constraints.py super_mario_bros/mario-sample-left super_mario_bros/mario-sample-right --save_filename mario-sample"
5. Run "python run_solver.py level_saved_files_block/prolog_files/mario-sample.pl config_mario-sample.json --max_sol 5 --print_level --save"

Try adjusting the config specifications in config_mario-sample.json (e.g. change the range of block tiles or the % range of tiles from each level)

### Saved filepaths
- metatile constraints files: "level_saved_files_block/metatile_constraints/"

- prolog files: "level_saved_files_block/prolog_files/"

- level structural txt files: "level_structural_layers/**game**/**level**.txt"
