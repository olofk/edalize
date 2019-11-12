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


    def _filelist_has_filetype(self, file_list, string, match_type='prefix'):
        for f in file_list:
            if match_type == 'prefix' and f.file_type.startswith(string):
                return True
            elif match_type == 'exact' and f.file_type == string:
                return True
        return False

    def configure_main(self):

        def _vcs_filelist_filter(src_file):
            ft = src_file.file_type
            # XXX: C source files can be passed to VCS to be compiled into DPI
            # libraries; passing C sources together with RTL sources is a
            # workaround until we have proper DPI support
            # (https://github.com/olofk/fusesoc/issues/311).
            return ft.startswith("verilogSource") or ft.startswith("systemVerilogSource") or ft == 'cSource' or ft == 'cppSource'

        self._write_fileset_to_f_file(os.path.join(self.work_root, self.name + '.scr'),
                                      include_vlogparams=True,
                                      filter_func=_vcs_filelist_filter)

        plusargs = []
        if self.plusarg:
            for key, value in self.plusarg.items():
                plusargs += ['+{}={}'.format(key, self._param_value_str(value))]

        vcs_options = self.tool_options.get('vcs_options', [])

        (src_files, incdirs) = self._get_fileset_files(force_slash=True)
        if self._filelist_has_filetype(src_files, 'systemVerilog', match_type = 'prefix'):
            vcs_options.append('-sverilog')

        if self._filelist_has_filetype(src_files, 'verilog2001', match_type = 'exact'):
            vcs_options.append('+v2k')

        template_vars = {
            'name'              : self.name,
            'vcs_options'       : vcs_options,
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
