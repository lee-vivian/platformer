'''
Outputs str command to run groundcollapse program with specified parameters
'''

from model.level import TILE_DIM
from utils import read_json, error_exit

if __name__ == "__main__":

    # Adjustable variables
    program = "main_platformer"
    training_level = "sample_mini"
    chunk_width = None
    chunk_height = None

    failure_millis = 3000
    save_chunks = False
    save_hr_chunks = False
    debug = True

    # Set display dimensions to training level dimensions
    if chunk_width is None or chunk_height is None:  # no alt chunk size specified
        display_w = None
        display_h = None
        all_levels_info_file = "../platformer/level_saved_files_block/all_levels_info.json"
        levels = read_json(all_levels_info_file).get('contents')
        for level_info in levels:
            if level_info.get('level_name') == training_level:
                display_w = level_info.get('level_width')
                display_h = level_info.get('level_height')
                break
        if display_w is None or display_h is None:
            error_exit("%s level not found in all_levels_info.json" % training_level)

        chunk_width = int(display_w / TILE_DIM)
        chunk_height = int(display_h / TILE_DIM)

    else:
        display_w = chunk_width * TILE_DIM
        display_h = chunk_height * TILE_DIM

    tileset = "tilesets/platformer/%s.json" % training_level
    scale_w = 1
    scale_h = 1

    command_str = "python %s.py --tileset %s --display_width %d --display_height %d " \
                  "--scale_width %d --scale_height %d --chunk_width %d --chunk_height %d --failureMillis %d" % \
                  (program, tileset, display_w, display_h, scale_w, scale_h, chunk_width, chunk_height,
                   failure_millis)

    if save_chunks or save_hr_chunks:
        command_str += " --levelName %s" % training_level
        if save_chunks:
            command_str += ' --saveChunks'
        if save_hr_chunks:
            command_str += ' --saveHumanReadableChunks'

    if debug:
        command_str += ' --debug'

    print(command_str)

