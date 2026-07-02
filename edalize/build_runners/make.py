from typing import List
from pathlib import Path

from edalize.utils import EdaCommands


class Make(object):
    def __init__(self, flow_options):
        self.build_options = flow_options.get("flow_make_options", [])

    def get_build_command(self):
        return ("make", self.build_options)

    def write(self, commands: EdaCommands, work_root: Path):
        commands.write(work_root / Path("Makefile"))
