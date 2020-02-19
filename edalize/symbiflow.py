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

- Constraints: unmanaged constraints with file_type SDC

"""

class Symbiflow(Edatool):

    argtypes = ['vlogdefine', 'vlogparam', 'generic']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "The Symbilow backend executes Yosys sythesis tool and VPR place and route. It can target multiple different FPGA vendors",
                    'members' : [
                        {'name' : 'part',
                         'type' : 'String',
                         'desc' : 'FPGA part number (e.g. xc7a50t)'},
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
        constraints = []

        for f in src_files:
            if f.file_type in ['verilogSource']:
                file_list.append(f.name)
            if f.file_type in ['SDC']:
                constraints.append(f.name)

        partname = self.tool_options.get('part', None)
        assert partname is not None, 'Missing required "partname" parameter'
        if 'xc7a' in partname:
            bitstream_device = 'artix7'
        if 'xc7z' in partname:
            bitstream_device = 'zynq7'
        if 'xc7k' in partname:
            bitstream_device = 'kintex7'

        makefile_params = {'top' : 'top',
                           'sources' : ' '.join(file_list),
                           'partname' : partname,
                           'bitstream_device' : bitstream_device,
                           'pcf' : ' '.join(constraints),
                           'builddir' : 'build',
                          }
        self.render_template('symbiflow-makefile.j2',
                             'Makefile',
                             makefile_params)


    def run_main(self):
        logger.info("Programming")
