import logging
import os

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

logger = logging.getLogger(__name__)

class Nextpnr_xilinx(Edatool):

    argtypes = []

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            yosys_help = Yosys.get_doc(api_ver)
            nextpnr_help = {
                "members": [
                    {
                        "name": "part",
                        "type": "String",
                        "desc": "FPGA part type (available: xc7a35tcpg236-1, xc7a35tcsg324-1, xc7z010clg400-1, xc7z020clg484-1)",
                    },
                    {
                        "name": "nextpnr_as_subtool",
                        "type": "bool",
                        "desc": "Determines if nextpnr is run as a part of bigger toolchain, or as a standalone tool",
                    },
                ],
                "lists": [
                    {
                        "name": "nextpnr_options",
                        "type": "String",
                        "desc": "Additional options for the implementation command",
                    },
                ],
            }

            combined_members = nextpnr_help["members"]
            combined_lists = nextpnr_help.get("lists", [])
            yosys_members = yosys_help["members"]
            yosys_lists = yosys_help["lists"]

            combined_members.extend(
                m
                for m in yosys_members
                if m["name"] not in [i["name"] for i in combined_members]
            )
            combined_lists.extend(
                l
                for l in yosys_lists
                if l["name"] not in [i["name"] for i in combined_lists]
            )

            return {
                "description": "Open source Place and Route tool targeting Xilinx FPGAs",
                "members": combined_members,
                "lists": combined_lists,
            }

    def get_file_type_name(self, ftype, files):
        name = None
        for f in files:
            if f.file_type in [ftype] and name is None:
                name = f.name
            elif f.file_type in [ftype]:
                logger.warning("Multiple %s files provided! Using the first one: %s" % (ftype, name))
            else:
                continue
        return name

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files()

        yosys_synth_options = self.tool_options.get('yosys_synth_options', '')
        yosys_edam = {
                'files'         : self.files,
                'name'          : self.name,
                'toplevel'      : self.toplevel,
                'parameters'    : self.parameters,
                'tool_options'  : {'yosys' : {
                                        'arch' : 'xilinx',
                                        'yosys_synth_options' : yosys_synth_options,
                                        'yosys_as_subtool' : True,
                                        }
                                }
                }

        yosys = getattr(import_module("edalize.yosys"), "Yosys")(
            yosys_edam, self.work_root
        )
        yosys.configure()

        part_of_toolchain = self.tool_options.get('nextpnr_as_subtool', False)
        chip_part = self.tool_options.get('part', '')

        if chip_part is '':
            logger.warning("Missing `part` name in tool_options!")

        # Check if we use custom chipDataBase file
        chipdb = self.get_file_type_name("chipDataBase", src_files)

        if chipdb is None:
            # Setup default chipdb
            default_path = os.path.join(os.environ["CONDA_PREFIX"], 'share', 'nextpnr-xilinx', chip_part + '.bin')
            if os.path.exists(default_path):
                chipdb = default_path
        else:
            logger.warning("Using custom chipDataBase file: %s" % (chipdb))

        xdc = self.get_file_type_name("xdc", src_files)

        if xdc is None:
            logger.error("ERROR: missing required XDC file!")
        if chipdb is None:
            logger.error("ERROR: missing required chipdb file! Please either install chipdb files using conda: `conda install -c symbiflow nextpnr-xilinx` and activate conda environment or provide `chipDataBase` file to edam.")

        template_vars = {
            "arch": "xilinx",
            "chipdb": chipdb,
            "constr": xdc,
            "name": self.name,
        }

        makefile_name = self.name + "-nextpnr-xilinx.mk" if part_of_toolchain else "Makefile"
        self.render_template("nextpnr-xilinx-makefile.j2", makefile_name, template_vars)
