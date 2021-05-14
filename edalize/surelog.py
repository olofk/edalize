import logging
import os.path

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Surelog(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Surelog",
                    'lists' : [
                        {'name' : 'surelog_options',
                         'type' : 'String',
                         'desc' : 'List of the Surelog parameters'},
                        ]}

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files()
        verilog_file_list = []
        systemverilog_file_list = []
        for f in src_files:
            if f.file_type.startswith('verilogSource'):
                verilog_file_list.append(f.name)
            if f.file_type.startswith('systemVerilogSource'):
                systemverilog_file_list.append("-sv " + f.name)

        surelog_options = self.tool_options.get('surelog_options', [])
        arch = self.tool_options.get('arch', None)

        pattern = len(self.vlogparam.keys()) * " -P%s=%%s"
        verilog_params_command = pattern % tuple(self.vlogparam.keys()) % tuple(self.vlogparam.values())

        verilog_defines_command = "+define" if self.vlogdefine.items() else ""
        pattern = len(self.vlogdefine.keys()) * "+%s=%%s"
        verilog_defines_command += pattern % tuple(self.vlogdefine.keys()) % tuple(self.vlogdefine.values())

        pattern = len(incdirs) * " -I%s"
        include_files_command = pattern % tuple(incdirs)


        template_vars = {
                'top'                       : self.toplevel,
                'name'                      : self.name,
                'sources'                   : ' '.join(verilog_file_list),
                'sv_sources'                : ' '.join(systemverilog_file_list),
                'arch'                      : arch,
                'verilog_params_command'    : verilog_params_command,
                'verilog_defines_command'   : verilog_defines_command,
                'include_files_command'     : include_files_command,
                'surelog_options'           : ' '.join(surelog_options),
        }


        self.render_template('surelog-makefile.j2',
                             'surelog.mk',
                             template_vars)
