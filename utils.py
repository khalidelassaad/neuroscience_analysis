import os
import sys


def get_child_folders(path):
    return_list = []
    for child_path in path.iterdir():
        if child_path.name[0] == ".":
            continue
        if not child_path.is_dir():
            continue
        return_list.append(child_path)
    return return_list


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
