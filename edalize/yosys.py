import os.path

from edalize.edatool import Edatool

class Yosys(Edatool):

    argtypes = ['vlogdefine', 'vlogparam']

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {'description' : "Open source synthesis tool many different FPGAs",
                    'members' : [
                        {'name' : 'arch',
                         'type' : 'String',
                         'desc' : 'Target architecture. Legal values are *xilinx*, *ice40*'},
                        {'name' : 'output_format',
                         'type' : 'String',
                         'desc' : 'Output file format. Legal values are *json*, *edif*, *blif*'}],
                    'lists' : [
                        {'name' : 'options',
                         'type' : 'String',
                         'desc' : 'Additional options for the synth command'},

                        {'name' : 'output_options',
                         'type' : 'String',
                         'desc' : 'Additional options for the write output command'},
                        ]}

    def configure_main(self):
        # write Yosys tcl script file
        (src_files, incdirs) = self._get_fileset_files()

        file_table = []
        for f in src_files:
            switch = ""
            if f.file_type in ['verilogSource']:
                switch = ""
            elif f.file_type in ['systemVerilogSource']:
                switch = "-sv"
            else:
                continue

            file_table.append('{{{file} {switch}}}'.format(file=f.name, switch=switch))

        output_format = self.tool_options.get('output_format', 'blif')
        template_vars = {
                'file_table'          : "{" + " ".join(file_table) + "}",
                'synth_command'       : "synth_" + self.tool_options.get('arch', 'xilinx'),
                'synth_options'       : self.tool_options.get('options', ''),
                'write_command'       : "write_" + output_format,
                'write_options'       : self.tool_options.get('output_options', ''),
                'default_target'      : output_format,
                'name'                : self.name
        }

        self.render_template('yosys-script-tcl.j2',
                             self.name + '.tcl',
                             template_vars)

        self.render_template('yosys-makefile.j2',
                             self.name + '.mk',
                             template_vars)
        #with open(os.path.join(self.work_root, self.name+'.tcl'), 'w') as yosys_file:

