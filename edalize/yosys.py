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
                        {'name' : 'synth_options',
                         'type' : 'String',
                         'desc' : 'Additional options for the synth command'}
                        ,

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

        verilog_defines = []
        for key, value in self.vlogdefine.items():
            verilog_defines.append('{{{key} {value}}}'.format(key=key, value=value))

        verilog_params = []
        for key, value in self.vlogparam.items():
            _s = "chparam -set {} {} \$abstract\{}"
            verilog_params.append(_s.format(key,
                self._param_value_str(value, '"'),
                self.toplevel))

        output_format = self.tool_options.get('output_format', 'blif')
        template_vars = {
                'verilog_defines'     : "{" + " ".join(verilog_defines) + "}",
				'verilog_params'	  : "\n".join(verilog_params),
                'file_table'          : "{" + " ".join(file_table) + "}",
                'incdirs'             : ' '.join(['-I'+d for d in incdirs]),
                'top'                 : self.toplevel,
                'synth_command'       : "synth_" + self.tool_options.get('arch', 'xilinx'),
                'synth_options'       : self.tool_options.get('options', ''),
                'write_command'       : "write_" + output_format,
                'default_target'      : output_format,
                'name'                : self.name
        }

        self.render_template('yosys-script-tcl.j2',
                             self.name + '.tcl',
                             template_vars)

        self.render_template('yosys-makefile.j2',
                             self.name + '.mk',
                             template_vars)

