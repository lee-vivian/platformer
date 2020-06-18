"""
Expressive range script - FILE DEPRECATED
"""

import argparse

tile_char_dict = {
    'block': 'X',
    'bonus': '?',
    'start': '*',
    'goal': '!',
    'empty': '-',
    'one_way_platform': 'T',
    'door': 'D',
    'hazard': 'H',
    'wall': 'W'
}

density_types = ['block', 'one_way_platform', 'wall']
interesting_types = ['bonus', 'door']
dangerous_types = ['hazard']


# Returns dictionary with expressive range metrics
def get_expressive_range(game, level):
    level_lines = get_level_lines(game, level)
    level_w = len(level_lines[0])
    level_h = len(level_lines)
    total_tiles = level_w * level_h

    expressive_range = {
        'density': density(level_lines, total_tiles),
        'leniency': leniency(level_lines, total_tiles),
        'interestingness': interestingness(level_lines, total_tiles)
    }

    print("----- EXPRESSIVE RANGE: %s/%s -----" % (game, level))
    for metric, value in expressive_range.items():
        print("%s: %f" % (metric, value))


# Returns list of elements where each element is a str representing a row of chars in the given level
def get_level_lines(game, level):
    level_lines = []
    filepath = "level_structural_layers/%s/%s.txt" % (game, level)
    f = open(filepath, 'r')
    for line in f:
        line = line.rstrip()
        level_lines.append(line)
    return level_lines


# Density = proportion of solid tiles in level
def density(level_lines, total_tiles):
    total = 0
    for line in level_lines:
        for tile_type in density_types:
            total += line.count(tile_char_dict[tile_type])
    return (total / total_tiles) * 100


# Leniency = proportion of non-dangerous tiles in level
def leniency(level_lines, total_tiles):
    total = 0
    for line in level_lines:
        num_dangerous_chars = 0
        for tile_type in dangerous_types:
            num_dangerous_chars += line.count(tile_char_dict[tile_type])
        total += len(line) - num_dangerous_chars
    return (total / total_tiles) * 100


# Interestingness = proportion of interesting tiles in level
def interestingness(level_lines, total_tiles):
    total = 0
    for line in level_lines:
        for tile_type in interesting_types:
            total += line.count(tile_char_dict[tile_type])
    return (total / total_tiles) * 100


# # TODO edit function
# def pathprop(level):
#     total = 0
#     for l in level:
#         total += l.count('P')
#     return ((total*100)/(16*16))
#
#
# # TODO edit function
# def nonlinearity(level):
#     try:
#         level = [[level[j][i] for j in range(len(level))] for i in range(len(level[0]))]
#     except:
#         print(level,len(level),len(level[0]))
#         sys.exit()
#     x = np.arange(16)
#     y = []
#     for i, lev in enumerate(level):
#         #print(i,lev)
#         appended = False
#         for j, l in enumerate(lev):
#             if l == 'S' or l =='#' or l == 'X' or l == 'M' or l == 'T' or l == 'B' or l == '|':
#                 y.append(16-j)
#                 appended = True
#                 break
#         if not appended:
#             y.append(0)
#     x = x.reshape(-1,1)
#     y = np.asarray(y)
#     #print(x.shape,y.shape)
#     #print(x)
#     #print(y)
#     reg = linear_model.LinearRegression()
#     reg.fit(x,y)
#     y_pred = reg.predict(x)
#     mse = mean_squared_error(y,y_pred)
#     return mse
#
#
#

def main(game, level):
    get_expressive_range(game, level)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get expressive range of a level')
    parser.add_argument('game', type=str, help='Name of the game')
    parser.add_argument('level', type=str, help='Name of the level')
    args = parser.parse_args()
    main(args.game, args.level)
