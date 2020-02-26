import logging
import os.path
import platform
import re
import subprocess

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

""" Symbiflow backtend

A core (usually the system core) can add the following files:

- Standard design sources (Verilog only)

- Constraints: unmanaged constraints with file_type SDC, pin_constraints with file_type SDF and placement constraints with file_type xdc

"""

class Symbiflow(Edatool):

    argtypes = ['vlogdefine', 'vlogparam', 'generic']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "The Symbilow backend executes Yosys sythesis tool and VPR place and route. It can target multiple different FPGA vendors",
                    'members' : [
                        {'name' : 'package',
                         'type' : 'String',
                         'desc' : 'FPGA chip package (e.g. clg400-1)'},
                        {'name' : 'part',
                         'type' : 'String',
                         'desc' : 'FPGA part type (e.g. xc7a50t)'},
                        {'name' : 'vendor',
                         'type' : 'String',
                         'desc' : 'Target architecture. Currently only "xilinx" is supported '},
                   ]}

    def get_version(self):
        return "1.0"


    def configure_main(self):
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
        makefile_params = {'top' : self.toplevel,
                           'sources' : ' '.join(file_list),
                           'partname' : partname,
                           'part' : part,
                           'bitstream_device' : bitstream_device,
                           'sdc' : ' '.join(timing_constraints),
                           'pcf' : ' '.join(pins_constraints),
                           'xdc' : ' '.join(placement_constraints),
                          }
        self.render_template('symbiflow-makefile.j2',
                             'Makefile',
                             makefile_params)


    def run_main(self):
        logger.info("Programming")
