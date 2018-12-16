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
        f = open(os.path.join(self.work_root, self.name+'.scr'),'w')

        (src_files, incdirs) = self._get_fileset_files()
        for key, value in self.vlogdefine.items():
            f.write('+define+{}={}\n'.format(key, self._param_value_str(value, '')))

        for key, value in self.vlogparam.items():
            f.write('+parameter+{}.{}={}\n'.format(self.toplevel, key, self._param_value_str(value, '"')))
        for id in incdirs:
            f.write("+incdir+" + id+'\n')
        for src_file in src_files:
            if (src_file.file_type.startswith("verilogSource") or src_file.file_type.startswith("systemVerilogSource")):
                f.write(src_file.name+'\n')
            elif src_file.file_type == 'user':
                pass
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(src_file.name, src_file.file_type))

        f.close()

        plusargs = []
        if self.plusarg:
            for key, value in self.plusarg.items():
                plusargs += ['+{}={}'.format(key, self._param_value_str(value))]

        template_vars = {
            'name'              : self.name,
            'tool_options'      : self.tool_options,
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
