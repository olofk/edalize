import os
import logging

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Vcs(Edatool):

    _description = """ Synopsys VCS Backend

VCS is one of the "Big 3" simulators.

Example snippet of a CAPI2 description file for VCS:

.. code:: yaml

   vcs:
     vcs_options:
       # Compile-time options passed to the vcs command
       - -debug_access+pp
       - -debug_access+all
     run_options:
       # Run-time options passed to the simulation itself
       - -licqueue
"""

    tool_options = {
        'lists' : {
            'vcs_options' : 'String', # compile-time options (passed to VCS)
            'run_options' : 'String', # runtime options (passed to simulation)
        }
    }

    argtypes = ['plusarg', 'vlogdefine', 'vlogparam']

    def configure_main(self):
        self._write_fileset_to_f_file(os.path.join(self.work_root, self.name + '.scr'),
                                      include_vlogparams = True)

        plusargs = []
        if self.plusarg:
            for key, value in self.plusarg.items():
                plusargs += ['+{}={}'.format(key, self._param_value_str(value))]

        template_vars = {
            'name'              : self.name,
            'vcs_options'       : self.tool_options.get('vcs_options', []),
            'run_options'       : self.tool_options.get('run_options', []),
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
