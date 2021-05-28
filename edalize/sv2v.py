import logging
import os.path

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Sv2v(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Sv2v",
                    'lists' : [
                        {'name' : 'sv2v_options',
                         'type' : 'String',
                         'desc' : 'List of the sv2v parameters'},
                        ]}

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files()
        systemverilog_file_list = []
        for f in src_files:
            if f.file_type.startswith('systemVerilogSource'):
                systemverilog_file_list.append(f.name)

        pattern = len(self.vlogdefine.keys()) * "-D%s=%%s "
        verilog_defines_command = pattern % tuple(self.vlogdefine.keys()) % tuple(self.vlogdefine.values())

        sv2v_options = self.tool_options.get('sv2v_options', [])

        template_vars = {
                'name'                      : self.name,
                'sv_sources'                : ' '.join(systemverilog_file_list),
                'incdirs'                   : ' '.join(['--incdir='+d for d in incdirs]),
                'sv2v_options'              : ' '.join(sv2v_options) + " " + verilog_defines_command,
        }


        self.render_template('sv2v-makefile.j2',
                             'sv2v.mk',
                             template_vars)

