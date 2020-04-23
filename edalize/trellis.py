import os.path

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

class Trellis(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            yosys_help = Yosys.get_doc(api_ver)
            trellis_help = {
                    'lists' : [
                        {'name' : 'nextpnr_options',
                         'type' : 'String',
                         'desc' : 'Additional options for nextpnr'},
                        {'name' : 'yosys_synth_options',
                         'type' : 'String',
                         'desc' : 'Additional options for the synth_ecp5 command'},
                        ]}

            combined_members = []
            combined_lists = trellis_help['lists']
            yosys_members = yosys_help['members']
            yosys_lists = yosys_help['lists']

            combined_members.extend(m for m in yosys_members if m['name'] not in [i['name'] for i in combined_members])
            combined_lists.extend(l for l in yosys_lists if l['name'] not in [i['name'] for i in combined_lists])

            return {'description' : "Project Trellis enables a fully open-source flow for ECP5 FPGAs using Yosys for Verilog synthesis and nextpnr for place and route",
                    'members' : combined_members,
                    'lists' : combined_lists}

    def configure_main(self):
        # Write yosys script file
        (src_files, incdirs) = self._get_fileset_files()
        yosys_synth_options = self.tool_options.get('yosys_synth_options', [])
        yosys_synth_options = ["-nomux"] + yosys_synth_options
        yosys_edam = {
                'files'         : self.files,
                'name'          : self.name,
                'toplevel'      : self.toplevel,
                'parameters'    : self.parameters,
                'tool_options'  : {'yosys' : {
                                        'arch' : 'ecp5',
                                        'yosys_synth_options' : yosys_synth_options,
                                        'yosys_as_subtool' : True,
                                        }
                                }
                }

        yosys = getattr(import_module("edalize.yosys"), 'Yosys')(yosys_edam, self.work_root)
        yosys.configure()

        lpf_files = []
        for f in src_files:
            if f.file_type == 'LPF':
                lpf_files.append(f.name)
            elif f.file_type == 'user':
                pass

        if not lpf_files:
            lpf_files = ['empty.lpf']
            with open(os.path.join(self.work_root, lpf_files[0]), 'a'):
                os.utime(os.path.join(self.work_root, lpf_files[0]), None)
        elif len(lpf_files) > 1:
            raise RuntimeError("trellis backend supports only one LPF file. Found {}".format(', '.join(lpf_files)))

        # Write Makefile
        nextpnr_options     = self.tool_options.get('nextpnr_options', [])
        template_vars = {
            'name'                : self.name,
            'lpf_file'            : lpf_files[0],
            'nextpnr_options'     : nextpnr_options,
        }
        self.render_template('trellis-makefile.j2',
                             'Makefile',
                             template_vars)
