import json
import pickle


def error_exit(msg):
    print(msg)
    exit(0)


def read_json(filepath):
    with open(filepath, 'r') as file:
        contents = json.load(file)
    file.close()
    return contents


def write_json(filepath, contents):
    with open(filepath, 'w') as file:
        json.dump(contents, file, indent=2, sort_keys=True)
    file.close()
    print("Saved to:", filepath)
    return filepath


def read_pickle(filepath):
    with open(filepath, 'rb') as file:
        contents = pickle.load(file)
    file.close()
    return contents


def write_pickle(filepath, contents):
    with open(filepath, 'wb') as file:
        pickle.dump(contents, file, protocol=pickle.HIGHEST_PROTOCOL)
    file.close()
    print("Saved to:", filepath)
    return filepath

