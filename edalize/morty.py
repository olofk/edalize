import os
import logging

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Morty(Edatool):
    argtypes = ['cmdlinearg', 'vlogdefine']

    _description = """ Morty Systemverilog pickle

Morty helps you package your SystemVerilog source files.
It does so by resolving all pre-processor macros, optionally
uniquifying module names and serializing them into a single
file. That avoids namespace conflicts and your hardware becomes
easier and more reliable to share!

Get `morty` from here: https://github.com/zarubaf/morty

.. code:: yaml

   morty:
     morty_options:
       # Run-time options passed to `morty` itself
        - -e, --exclude <MODULE>...    Add modules which should not be renamed
        - -p, --prefix <PREFIX>        Prepend a name to all global names
        - -s, --suffix <SUFFIX>        Append a name to all global names
"""

    tool_options = {
        'lists' : {
            'morty_options' : 'String', # runtime options (passed to morty)
        }
    }

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Run the (System-) Verilog pickle tool called `morty`.",
                    'lists' : [
                        {'name' : 'morty_options',
                         'type' : 'String',
                         'desc' : 'Run-time options passed to morty.'},
                        ]}

    def build_main(self, target=None):
        args = list()
        src_files_filtered = list()
        (src_files, incdirs) = self._get_fileset_files()

        args += ['-I {}'.format(incdir) for incdir in incdirs]
        args += ['-D {}={}'.format(key, self._param_value_str(value)) for key, value in self.vlogdefine.items()]

        # Filter for Verilog source files.
        for src_file in src_files:
            if Edatool._filter_verilog_files(src_file):
                src_files_filtered.append(src_file)

        # Append filtered file names.
        args += [f.name for f in src_files_filtered]
        # Append any options passed through `morty_options`.
        args += self.tool_options.get('morty_options', [])
        # Go and do your thing!
        self._run_tool('morty', args, quiet=True)

    def run_main(self):
        logger.warn("Morty does not support running. Use build instead.")
