import os.path

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

class Apicula(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            yosys_help = Yosys.get_doc(api_ver)
            apicula_help = {
                    'lists' : [
                        {'name' : 'nextpnr_options',
                         'type' : 'String',
                         'desc' : 'Additional options for nextpnr'},
                        {'name' : 'yosys_synth_options',
                         'type' : 'String',
                         'desc' : 'Additional options for the synth_gowin command'},
                        ]}

            combined_members = []
            combined_lists = apicula_help['lists']
            yosys_members = yosys_help['members']
            yosys_lists = yosys_help['lists']

            combined_members.extend(m for m in yosys_members if m['name'] not in [i['name'] for i in combined_members])
            combined_lists.extend(l for l in yosys_lists if l['name'] not in [i['name'] for i in combined_lists])

            return {'description' : "Open source toolchain for Gowin FPGAs. Uses yosys for synthesis and nextpnr for Place & Route",
                    'members' : combined_members,
                    'lists' : combined_lists}

    def configure_main(self):
        # Write yosys script file
        (src_files, incdirs) = self._get_fileset_files()
        yosys_synth_options =  self.tool_options.get('yosys_synth_options',[])
        yosys_synth_options = ["-json " + self.name +".json" + " -top " + self.toplevel + " " ] + yosys_synth_options  #Need to add -json and -top after synth_gowin 
        yosys_edam = {
                'files'         : self.files,
                'name'          : self.name,
                'toplevel'      : self.toplevel,
                'parameters'    : self.parameters,
                'tool_options'  : {'yosys' : {
                                        'arch' : 'gowin',
                                        'yosys_synth_options' : yosys_synth_options,
                                        'yosys_as_subtool' : True,
                                        }
                                }
                }

        yosys = getattr(import_module("edalize.yosys"), 'Yosys')(yosys_edam, self.work_root)
        yosys.configure()

        cst_files = []
        for f in src_files:
            if f.file_type == 'CST':
                cst_files.append(f.name)
            elif f.file_type == 'user':
                pass

        if not cst_files:
            cst_files = ['empty.cst']
            with open(os.path.join(self.work_root, cst_files[0]), 'a'):
                os.utime(os.path.join(self.work_root, cst_files[0]), None)
        elif len(cst_files) > 1:
            raise RuntimeError("Apicula backend supports only one CST file. Found {}".format(', '.join(cst_files)))

        # Write Makefile
        nextpnr_options     = self.tool_options.get('nextpnr_options', [])
        template_vars = {
            'name'                : self.name,
            'cst_file'            : cst_files[0],
            'nextpnr_options'     : nextpnr_options,
        }
        self.render_template('apicula-makefile.j2',
                             'Makefile',
                             template_vars)
