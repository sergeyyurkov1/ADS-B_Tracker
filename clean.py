import os
import shutil

EXCLUDED_DIRS = [
    ".venv",
    ".git",
]  # exclude __pycache__ directories inside these folders
DIRS_TO_DELETE = ["__pycache__"]


def delete_folders(folders: list, exclude: list, path: str = ".") -> None:
    for root, _, _ in os.walk(path):
        try:
            root_dir = root.split("\\")[1]
            end_dir = root.rsplit("\\", 1)[1]

            if root_dir not in exclude and end_dir in folders:
                print(root)

                try:
                    shutil.rmtree(root)
                except (PermissionError, FileNotFoundError):
                    pass

        except IndexError:  # root dir
            pass
        except Exception as e:
            print(e)


delete_folders(folders=DIRS_TO_DELETE, exclude=EXCLUDED_DIRS)
