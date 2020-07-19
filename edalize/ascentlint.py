import logging
import re
import os
from collections import OrderedDict

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Ascentlint(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : """ Real Intent Ascent Lint backend

Ascent Lint performs static source code analysis on HDL code and checks for
common coding errors or coding style violations.
""",
                    'lists' : [
                        {'name' : 'ascentlint_options',
                         'type' : 'String',
                         'desc' : 'Additional run options for ascentlint'}
                    ]}

    def configure_main(self):
        (src_files, incdirs) = self._get_fileset_files(force_slash=True)

        self._write_fileset_to_f_file(os.path.join(self.work_root, 'sources.f'),
                                      include_vlogparams = False)

        tcl_source_files = [f for f in src_files if f.file_type == 'tclSource']
        waiver_files = [f for f in src_files if f.file_type == 'waiver']

        template_vars = {
            'name'             : self.name,
            'ascentlint_options' : ' '.join(self.tool_options.get('ascentlint_options', [])),
            'tcl_source_files' : tcl_source_files,
            'waiver_files'     : waiver_files,
            'toplevel'         : self.toplevel,
            'vlogparam'        : self.vlogparam,
        }

        self.render_template('run-ascentlint.tcl.j2',
                             'run-ascentlint.tcl',
                             template_vars)

        self.render_template('Makefile.j2',
                             'Makefile',
                             template_vars)
