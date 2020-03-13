'''
Outputs str command to run groundcollapse program with specified parameters
'''

from model.level import TILE_DIM

if __name__ == "__main__":

    level = "sample_small"
    tileset = "../platformer/level_saved_files_block/metatile_constraints/%s.json" % level
    constraint_pl = "wfc_platformer.pl"

    scale_w = 1
    scale_h = 1
    size = 8  # n in nxn chunk
    display_w = size * TILE_DIM
    display_h = size * TILE_DIM
    failure_millis = 2000
    save_chunks = False
    save_hr_chunks = False
    debug = False

    command_str = "python main.py --path %s --tileset %s --display_width %d --display_height %d " \
                  "--scale_width %d --scale_height %d --size %d --failureMillis %d" % \
                  (constraint_pl, tileset, display_w, display_h, scale_w, scale_h, size, failure_millis)

    if save_chunks or save_hr_chunks:
        command_str += " --levelName %s" % level
        if save_chunks:
            command_str += ' --saveChunks'
        if save_hr_chunks:
            command_str += ' --saveHumanReadableChunks'

    if debug:
        command_str += ' --debug'

    print(command_str)

