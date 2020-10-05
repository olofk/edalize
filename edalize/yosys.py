import logging
import os.path

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Yosys(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Open source synthesis tool targeting many different FPGAs",
                    'members' : [
                        {'name' : 'arch',
                         'type' : 'String',
                         'desc' : 'Target architecture. Legal values are *xilinx*, *ice40* and *ecp5*'},
                        {'name' : 'output_format',
                         'type' : 'String',
                         'desc' : 'Output file format. Legal values are *json*, *edif*, *blif*'},
                        {'name' : 'yosys_as_subtool',
                         'type' : 'bool',
                         'desc' : 'Determines if Yosys is run as a part of bigger toolchain, or as a standalone tool'},
                        {'name' : 'makefile_name',
                         'type' : 'String',
                         'desc' : 'Generated makefile name, defaults to $name.mk'},
                        {'name' : 'script_name',
                         'type' : 'String',
                         'desc' : 'Generated tcl script filename, defaults to $name.mk'},
                        ],
                    'lists' : [
                        {'name' : 'yosys_synth_options',
                         'type' : 'String',
                         'desc' : 'Additional options for the synth command'},
                        ]}

    def configure_main(self):
        # write Yosys tcl script file
        (src_files, incdirs) = self._get_fileset_files()
        part_of_toolchain = self.tool_options.get('yosys_as_subtool', False)

        file_table = []
        for f in src_files:
            cmd = ""
            if f.file_type.startswith('verilogSource'):
                cmd = 'read_verilog'
            elif f.file_type.startswith('systemVerilogSource'):
                cmd = 'read_verilog -sv'
            elif f.file_type == 'tclSource':
                cmd = 'source'
            else:
                continue

            file_table.append(cmd + ' {' + f.name + '}')

        verilog_defines = []
        for key, value in self.vlogdefine.items():
            verilog_defines.append('{{{key} {value}}}'.format(key=key, value=value))

        verilog_params = []
        for key, value in self.vlogparam.items():
            if type(value) is str:
                value = "{\"" + value + "\"}"
            _s = r"chparam -set {} {} {}"
            verilog_params.append(_s.format(key,
                self._param_value_str(value),
                self.toplevel))

        output_format = self.tool_options.get('output_format', 'blif')
        arch = self.tool_options.get('arch', None)

        if not arch:
            logger.error("ERROR: arch is not defined.")

        makefile_name = self.tool_options.get('makefile_name', self.name + '.mk')
        script_name = self. tool_options.get('script_name', self.name + '.tcl')
        template_vars = {
                'verilog_defines'     : "{" + " ".join(verilog_defines) + "}",
                'verilog_params'      : "\n".join(verilog_params),
                'file_table'          : "\n".join(file_table),
                'incdirs'             : ' '.join(['-I'+d for d in incdirs]),
                'top'                 : self.toplevel,
                'synth_command'       : "synth_" + arch,
                'synth_options'       : " ".join(self.tool_options.get('yosys_synth_options', '')),
                'write_command'       : "write_" + output_format,
                'default_target'      : output_format,
                'edif_opts'           : '-pvector bra' if arch=='xilinx' else '',
                'script_name'         : script_name,
                'name'                : self.name
        }

        self.render_template('yosys-script-tcl.j2',
                             script_name,
                             template_vars)

        makefile_name = self.name + '.mk' if part_of_toolchain else 'Makefile'
        self.render_template('yosys-makefile.j2',
                             makefile_name,
                             template_vars)

