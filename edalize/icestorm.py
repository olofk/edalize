import os.path

from edalize.edatool import Edatool
from edalize.yosys import Yosys
from importlib import import_module

class Icestorm(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Open source toolchain for Lattice iCE40 FPGAs. Uses yosys for synthesis and arachne-pnr or nextpnr for Place & Route",
                    'members' : [
                        {'name' : 'pnr',
                         'type' : 'String',
                         'desc' : 'Select Place & Route tool. Legal values are *arachne* for Arachne-PNR or *next* for nextpnr. Default is arachne'}],
                    'lists' : [
                        {'name' : 'arachne_pnr_options',
                         'type' : 'String',
                         'desc' : 'Additional options for Arachnhe PNR'},
                        {'name' : 'nextpnr_options',
                         'type' : 'String',
                         'desc' : 'Additional options for nextpnr'},
                        {'name' : 'yosys_synth_options',
                         'type' : 'String',
                         'desc' : 'Additional options for the synth_ice40 command'},
                        ]}

    def configure_main(self):
        # Write yosys script file
        (src_files, incdirs) = self._get_fileset_files()
        yosys_edam = {
                'files'         : self.files,
                'vlogdefine'    : self.vlogdefine,
                'vlogparam'     : self.vlogparam,
                'name'          : self.name,
                'toplevel'      : self.toplevel,
                'tool_options'  : {'yosys' : {
                                        'arch' : 'ice40',
                                        'synth_options' : self.yosys_synth_options,
                                        'verilog_defines' : self.vlogdefine,
                                        'incdirs' : incdirs }
                                }
                }

        yosys = getattr(import_module("edalize.yosys"), 'Yosys')(yosys_edam, self.work_root)
        yosys.configure("")

        pcf_files = []
        for f in src_files:
            if f.file_type == 'PCF':
                pcf_files.append(f.name)
            elif f.file_type == 'user':
                pass

        if not pcf_files:
            pcf_files = ['empty.pcf']
            with open(os.path.join(self.work_root, pcf_files[0]), 'a'):
                os.utime(os.path.join(self.work_root, pcf_files[0]), None)
        elif len(pcf_files) > 1:
            raise RuntimeError("Icestorm backend supports only one PCF file. Found {}".format(', '.join(pcf_files)))

        pnr = self.tool_options.get('pnr', 'arachne')
        part = self.tool_options.get('part', None)
        if not pnr in ['arachne', 'next', 'none']:
            raise RuntimeError("Invalid pnr option '{}'. Valid values are 'arachne' for Arachne-pnr or 'next' for nextpnr".format(pnr))
        # Write Makefile
        arachne_pnr_options = self.tool_options.get('arachne_pnr_options', [])
        nextpnr_options     = self.tool_options.get('nextpnr_options', [])
        template_vars = {
            'name'                : self.name,
            'pcf_file'            : pcf_files[0],
            'pnr'                 : pnr,
            'arachne_pnr_options' : arachne_pnr_options,
            'nextpnr_options'     : nextpnr_options,
            'default_target'      : 'json' if pnr == 'none' else 'bin',
            'device'              : part,
        }
        self.render_template('icestorm-makefile.j2',
                             'Makefile',
                             template_vars)
