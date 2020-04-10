import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

logger = logging.getLogger(__name__)

""" Symbiflow backtend

A core (usually the system core) can add the following files:

- Standard design sources (Verilog only)

- Constraints: unmanaged constraints with file_type SDC, pin_constraints with file_type PCF and placement constraints with file_type xdc

"""

class Symbiflow(Edatool):

    argtypes = ['vlogdefine', 'vlogparam', 'generic']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            symbiflow_help = {
                    'members' : [
                        {'name' : 'package',
                         'type' : 'String',
                         'desc' : 'FPGA chip package (e.g. clg400-1)'},
                        {'name' : 'part',
                         'type' : 'String',
                         'desc' : 'FPGA part type (e.g. xc7a50t)'},
                        {'name' : 'builddir',
                         'type' : 'String',
                         'desc' : 'directory where all the intermediate files will be stored (default "build")'},
                        {'name' : 'vendor',
                         'type' : 'String',
                         'desc' : 'Target architecture. Currently only "xilinx" is supported'},
                        {'name' : 'pnr',
                         'type' : 'String',
                         'desc' : 'Place and Route tool. Currently only "vpr" and "nextpnr" are supported'},
                   ]}

            symbiflow_members = symbiflow_help['members']

            return {'description' : "The Symbilow backend executes Yosys sythesis tool and VPR place and route. It can target multiple different FPGA vendors",
                    'members': symbiflow_members}

    def get_version(self):
        return "1.0"

    def configure_nextpnr(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        nextpnr_edam = {
                'files'         : self.files,
                'name'          : self.name,
                'toplevel'      : self.toplevel,
                'tool_options'  : {'nextpnr' : {
                                        'arch' : 'xilinx',
                                        'nextpnr_as_subtool' : True,
                                        }

                                }
                }

        nextpnr = getattr(import_module("edalize.nextpnr"), 'Nextpnr')(nextpnr_edam, self.work_root)
        nextpnr.configure(self.args)

        builddir = self.tool_options.get('builddir', 'build')

        part = self.tool_options.get('part', None)
        package = self.tool_options.get('package', None)

        assert part is not None, 'Missing required "part" parameter'
        assert package is not None, 'Missing required "package" parameter'

        partname = part + package

        if 'xc7a' in part:
            bitstream_device = 'artix7'
        if 'xc7z' in part:
            bitstream_device = 'zynq7'
        if 'xc7k' in part:
            bitstream_device = 'kintex7'

        makefile_params = {
                'top' : self.name,
                'partname' : partname,
                'bitstream_device' : bitstream_device,
                'builddir' : builddir,
            }

        self.render_template('symbiflow-nextpnr-makefile.j2',
                             'Makefile',
                             makefile_params)

    def configure_vpr(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        has_vhdl     = 'vhdlSource'      in [x.file_type for x in src_files]
        has_vhdl2008 = 'vhdlSource-2008' in [x.file_type for x in src_files]

        assert (not has_vhdl and not has_vhdl2008), 'VHDL files are not supported in Yosys'
        file_list = []
        timing_constraints = []
        pins_constraints = []
        placement_constraints = []
        user_files = []

        for f in src_files:
            if f.file_type in ['verilogSource']:
                file_list.append(f.name)
            if f.file_type in ['SDC']:
                timing_constraints.append(f.name)
            if f.file_type in ['PCF']:
                pins_constraints.append(f.name)
            if f.file_type in ['xdc']:
                placement_constraints.append(f.name)
            if f.file_type in ['user']:
                user_files.append(f.name)

        builddir = self.tool_options.get('builddir', 'build')

        # copy user files to builddir
        for f in user_files:
            shutil.copy(f, self.work_root + "/" + builddir)

        part = self.tool_options.get('part', None)
        package = self.tool_options.get('package', None)

        assert part is not None, 'Missing required "part" parameter'
        assert package is not None, 'Missing required "package" parameter'

        if 'xc7a' in part:
            bitstream_device = 'artix7'
        if 'xc7z' in part:
            bitstream_device = 'zynq7'
        if 'xc7k' in part:
            bitstream_device = 'kintex7'

        partname = part + package

        # a35t are in fact a50t
        # leave partname with 35 so we access correct DB
        if part == 'xc7a35t':
            part = 'xc7a50t'

        makefile_params = {'top' : self.toplevel,
                           'sources' : ' '.join(file_list),
                           'partname' : partname,
                           'part' : part,
                           'bitstream_device' : bitstream_device,
                           'sdc' : ' '.join(timing_constraints),
                           'pcf' : ' '.join(pins_constraints),
                           'xdc' : ' '.join(placement_constraints),
                           'builddir' : builddir,
                          }
        self.render_template('symbiflow-vpr-makefile.j2',
                             'Makefile',
                             makefile_params)

    def configure_main(self):
        if self.tool_options.get('pnr') == 'nextpnr':
            self.configure_nextpnr()
        else:
            self.configure_vpr()


    def run_main(self):
        logger.info("Programming")
