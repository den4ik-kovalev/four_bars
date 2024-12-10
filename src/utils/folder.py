import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Union


class Folder:

    def __init__(self, path: Union[str, Path], auto_create=False) -> None:
        self._path = Path(path)
        if auto_create:
            os.makedirs(self._path, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def name(self):
        return self._path.name

    def exists(self) -> bool:
        return self._path.exists()

    def clear(self):
        for child in self._path.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    def subdirs(self) -> list[Path]:
        return [x for x in self._path.iterdir() if x.is_dir()]

    def files(self) -> list[Path]:
        return [x for x in self._path.iterdir() if x.is_file()]

    def contains_filename(self, filename: str) -> bool:
        for filepath in self.files():
            if filepath.name == filename:
                return True
        return False

    @contextmanager
    def clear_after(self):
        try:
            yield
        finally:
            self.clear()

    def find_by_suffix(self, suffix: str) -> list[Path]:
        return [
            child for child in self._path.iterdir()
            if child.suffix == suffix
        ]

    def find_by_name(self, name: str) -> list[Path]:
        return [
            child for child in self._path.iterdir()
            if child.name == name
        ]
