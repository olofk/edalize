from unittest.mock import MagicMock

class Library(MagicMock):
    def add_source_files(self, file):
        print("add_source_files()")

class VUnit(MagicMock):
    @staticmethod
    def from_argv():
        return VUnit()

    def add_library(self):
        print("add_library()")
        return Library()