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

    def _create_python_path(self):
        (src_files, incdirs) = self._get_fileset_files()
        print(src_files)

        path_components = set()

        for f in src_files:
            if f.file_type is 'pythonSource':
                component = os.path.dirname(f.name)
                if component != '':
                    path_components.add(component)
                    
        return ':'.join(path_components)

    def configure_main(self):
        python_path = self._create_python_path()
        self.render_template(self.makefile_template, 'Makefile', {
            'python_path' : python_path})

    def run_main(self):
        self._run_tool('make', ['run'])