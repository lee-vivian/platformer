from matplotlib import pyplot as plt
import seaborn as sns
import pandas as pd
import argparse

METATILE_TYPES = ["start", "goal", "block", "bonus", "empty", "one_way_platform", "hazard", "wall",
                  "permeable_wall"]


def error_exit(msg):
    print("ERROR: %s" % msg)
    exit(0)


def main(csv_file, tile_type1, tile_type2, jitter):

    if tile_type1.lower() not in METATILE_TYPES or tile_type2 not in METATILE_TYPES:
        error_exit("Tile type must be one of: %s" % str(METATILE_TYPES))

    df = pd.read_csv(csv_file)
    x_col = "%s Tiles" % tile_type1.capitalize()
    y_col = "%s Tiles" % tile_type2.capitalize()
    if x_col not in df.columns:
        error_exit("%s column does not exist in the given csv file" % x_col)
    if y_col not in df.columns:
        error_exit("%s column does not exist in the given csv file" % y_col)

    ax = sns.stripplot(x=x_col, y=y_col, hue='Rules', data=df, jitter=jitter)
    ax.set_title('Expressive Range Rules Comparison')
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot scatterplot of ER trial results for new vs old rules')
    parser.add_argument('csv_file', type=str, help="Filepath to csv file")
    parser.add_argument('tile_type1', type=str, help="Tile type on x-axis")
    parser.add_argument('tile_type2', type=str, help="Tile type on y-axis")
    parser.add_argument('--jitter', const=True, nargs='?', type=bool, default=False, help='Add jitter to scatterplot')
    args = parser.parse_args()
    main(args.csv_file, args.tile_type1, args.tile_type2, args.jitter)
