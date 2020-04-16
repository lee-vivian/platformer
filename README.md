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


### II. Playing the game

Run "python main.py **environment** **game** **level**"

Run "python main.py --help" for a full list of options available (includes drawing metatile labels and solution paths)


### IIIa. Processing a new level individually (Creating metatile constraints file from a single level)
- Save level structural txt file in "level_structural_layers/**game**/**level**.txt" (see txt file format in [TheVGLC](https://github.com/TheVGLC/TheVGLC) for examples)  
  
- Run "python main.py **environment** **game** **level** --process"

### IIIb: Creating combined metatile constraints file from multiple levels
- Enumerate state graphs for each level individually  
  This step is already done if you've already run main.py on the level) else run "python enumerate.py **game** **level**"  
  
- Run "python combine_constraints.py **save_filename** --games **game1 game2 ...** --levels **level1 level2 ...**"  

### IV: Generating new levels from a metatile constraints file
- Create prolog file from the specified metatile_constraints file
  - Run "python gen_prolog.py **metatile_constraints_filepath**"

- Run clingo solver  
  - Run "python run_solver.py **prolog_filepath** **level_width** **level_height** --max_sol **num_levels_to_generate**" (level width and height are measured in tile units)  
  - Run "python run_solver.py --help" for a full list of options available (includes saving and validating generated levels)


### Saved filepaths
- metatile constraints files: "level_saved_files_block/metatile_constraints/"

- prolog files: "level_saved_files_block/prolog_files/"

- level structural txt files: "level_structural_layers/**game**/**level**.txt"
