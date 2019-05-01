import os
import logging

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Vcs(Edatool):

    tool_options = {
        'lists' : {'vcs_options' : 'String'}
    }

    argtypes = ['plusarg', 'vlogdefine', 'vlogparam']

    def configure_main(self):
        self._write_fileset_to_f_file(os.path.join(self.work_root, self.name + '.scr'))

        plusargs = []
        if self.plusarg:
            for key, value in self.plusarg.items():
                plusargs += ['+{}={}'.format(key, self._param_value_str(value))]

        template_vars = {
            'name'              : self.name,
            'tool_options'      : self.tool_options.get('vcs_options', []),
            'toplevel'          : self.toplevel,
            'plusargs'          : plusargs
        }

        self.render_template('Makefile.j2', os.path.join(self.work_root, 'Makefile'), template_vars)

    def run_main(self):
        args = ['run']

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ['+{}={}'.format(key, self._param_value_str(value))]
            args.append('EXTRA_OPTIONS='+' '.join(plusargs))

        self._run_tool('make', args)
