import logging
import os.path
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Cocotb(Edatool):

    makefile_template = 'cocotb-makefile.j2'

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Cocotb",
                    'lists' : [
                        {'name' : 'simulator',
                         'type' : 'String',
                         'desc' : 'The simulator for Cocotb to use'},
                        ]}


    def configure_main(self):
        self.render_template(self.makefile_template, 'Makefile', {})

    def run_main(self):
        self._run_tool('make', ['run'])