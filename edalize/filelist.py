# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os, sys, re
import logging

from edalize.edatool import Edatool
from pathlib import Path

logger = logging.getLogger(__name__)


class Filelist(Edatool):

    # Currently only +define+ is supported in the VC file. Some tools allow parameters to be passed but the syntax is tool specific.
    argtypes = ["vlogdefine"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The filelist backend writes out a VC file to be used in tool flows not yet supported by Edalize",
                "members": [
                    {
                        "name": "outpath",
                        "type": "String",
                        "desc": "Specify the output path for the VC file, can be absolute or relative to parent core file",
                    },
                    {
                        "name": "mode",
                        "type": "String",
                        "desc": "Select the output path style.  Legal values are *absolute* or *relative*",
                    },
                ],
                "lists": [
                    {
                        "name": "libext",
                        "type": "String",
                        "desc": "Provide a list of library extensions",
                    }
                ],
            }

    def configure_main(self):

        core_file = Path(self.edam["top_core"])
        core_name = core_file.name
        core_path = core_file.parent

        # If the user hasn't specified an output path, then default to the top core file location.
        # REVISIT: should the default be to write the VC file to the working directory?
        if not "outpath" in self.tool_options:
            self.tool_options["outpath"] = core_path
        else:
            outpath = self.tool_options["outpath"]

            if outpath.startswith("/"):
                # outpath is absolute
                self.tool_options["outpath"] = Path(outpath)
            elif outpath.startswith("$"):
                # outpath is using environment variable
                self.tool_options["outpath"] = Path(self._resolve_env_var(outpath))
            else:
                # outpath is relative to core_file
                self.tool_options["outpath"] = core_path / outpath

            logger.debug("outpath={}".format(self.tool_options["outpath"]))

        if self.tool_options["outpath"].suffix != "":
            # If the user has sepcified a full path with a filename, then use that...
            outfile = self.tool_options["outpath"]
        else:
            # ...else use the name of the core file.
            outfile = self.tool_options["outpath"] / core_name.replace(".core", ".f")

        # Validate the filelist mode
        # REVISIT: if we are writing to the working directory, what file paths should be used?
        mode = self.tool_options.get("mode", "absolute")
        if mode not in ["absolute", "relative"]:
            raise RuntimeError('Illegal filelist mode "{}"'.format(mode))

        # Write out the VC file
        with outfile.open("w") as f:
            for libext in self.tool_options.get("libext", []):
                f.write("+libext+{}\n".format(libext))

            (src_files, incdirs) = self._convert_paths(
                *self._get_fileset_files(force_slash=True), mode
            )

            for key, value in self.vlogdefine.items():
                define_str = self._param_value_str(param_value=value)
                f.write("+define+{}={}\n".format(key, define_str))

            for id in incdirs:
                f.write("+incdir+" + id + "\n")

            for src_file in src_files:
                if src_file.file_type.startswith(
                    "systemVerilogSource"
                ) or src_file.file_type.startswith("verilogSource"):
                    f.write(src_file.name + "\n")

        logger.info("wrote filelist to {}".format(outfile))

    def build(self):
        pass

    def run(self, args):
        pass

    def _resolve_env_var(self, outpath):
        """Resolves an environment variable in a path.

        The argument `outpath` should be an environment variable, $VAR, or a concatenated path of the
        form $VAR/the/rest/of/the/path.

        Assumes that an environment variable will be of the form $VAR, $(VAR) or ${VAR}.  The variable
        itself will normally be of the form VAR or SOME_VAR but all alphanumeric names with underscores
        will be detected.

        """

        regex = re.compile(
            r"""(\$                  #
                               (?:[({])?            # An optional opening brace or parnthesis
                               ([A-Za-z0-9_]+)      # The environment variable
                               (?:[)}])?            # An optional closing brace or parenthesis
                               (?:(/.+))?           # The rest of the path if there is one
                               $)""",
            re.VERBOSE,
        )

        if match := regex.match(outpath):
            envvar = match.group(2)
            therest = match.group(3)
            try:
                return os.environ[envvar] + (therest if therest else "")
            except KeyError:
                logger.error(
                    'could not resolve environment variable in outpath="{}"'.format(
                        match.group(1)
                    )
                )
                raise RuntimeError()
        else:
            logger.error(
                'did not recognise environment variable in outpath="{}"'.format(outpath)
            )
            raise RuntimeError()

    def _convert_paths(self, src_files, incdirs, mode):
        """Converts the work_root relative file paths to absolute or core file relative.

        The `src_files` and `incdirs` lists returned from `_get_fileset_files` are relative paths to
        the FuseSoC working directory, `work_root`.  This isn't particularly usefull for a generic
        VC file so we convert them to either absolute paths or relative to the parent core file.

        """
        _src_files = []
        _incdirs = []

        for src_file in src_files:
            src_file.name = self._resolve_path(
                Path(self.work_root) / src_file.name, mode
            )
            _src_files.append(src_file)

        for incdir in incdirs:
            _incdirs.append(self._resolve_path(Path(self.work_root) / incdir, mode))

        return (_src_files, _incdirs)

    def _resolve_path(self, path, mode):
        """Generates correct file paths.

        Depending on the `mode` selected, we can generate absolute file paths or ones relative
        to the output path where the .f file will be placed.

        """
        if mode == "absolute":
            return str(path.resolve())
        elif mode == "relative":
            return os.path.relpath(
                path.resolve(), start=self.tool_options["outpath"].resolve()
            )
        else:
            raise RuntimeError("illegal mode {}".format(mode))
