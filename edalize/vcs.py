import os
import logging

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

class Vcs(Edatool):

    tool_options = {
        'lists' : {'vcs_options' : 'String'}
    }

    argtypes = ['plusarg', 'vlogdefine', 'vlogparam']

    MAKEFILE_TEMPLATE = """
all: $(TARGET)

$(TARGET):
	vcs -full64 -t $(TOPLEVEL) -f $(TARGET).scr -o $@ $(VCS_OPTIONS)

run: $(TARGET)
	$(TARGET) -l vcs.log $(EXTRA_OPTIONS)

clean:
	$(RM) $(TARGET)
"""

    def configure_main(self):
        f = open(os.path.join(self.work_root, self.name+'.scr'),'w')

        (src_files, incdirs) = self._get_fileset_files()
        for key, value in self.vlogdefine.items():
            f.write('+define+{}={}\n'.format(key, self._param_value_str(value, '')))

        for key, value in self.vlogparam.items():
            f.write('+parameter+{}.{}={}\n'.format(self.toplevel, key, self._param_value_str(value, '"')))
        for id in incdirs:
            f.write("+incdir+" + id+'\n')
        timescale = self.tool_options.get('timescale')
        if timescale:
            with open(os.path.join(self.work_root, 'timescale.v'), 'w') as tsfile:
                tsfile.write("`timescale {}\n".format(timescale))
            f.write('timescale.v\n')
        for src_file in src_files:
            if src_file.file_type in ["verilogSource",
		                      "verilogSource-95",
		                      "verilogSource-2001",
		                      "verilogSource-2005",
                                      "systemVerilogSource",
			              "systemVerilogSource-3.0",
			              "systemVerilogSource-3.1",
			              "systemVerilogSource-3.1a"]:
                f.write(src_file.name+'\n')
            elif src_file.file_type == 'user':
                pass
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(src_file.name, src_file.file_type))

        f.close()

        with open(os.path.join(self.work_root, 'Makefile'), 'w') as f:

            f.write("TARGET           := {}\n".format(self.name))
            f.write("TOPLEVEL         := {}\n".format(self.toplevel))
            f.write("VCS_OPTIONS := {}\n".format(' '.join(self.tool_options.get('vcs_options', []))))
            if self.plusarg:
                plusargs = []
                for key, value in self.plusarg.items():
                    plusargs += ['+{}={}'.format(key, self._param_value_str(value))]
                f.write("EXTRA_OPTIONS    ?= {}\n".format(' '.join(plusargs)))

            f.write(self.MAKEFILE_TEMPLATE)

    def run_main(self):
        args = ['run']

        # Set plusargs
        if self.plusarg:
            plusargs = []
            for key, value in self.plusarg.items():
                plusargs += ['+{}={}'.format(key, self._param_value_str(value))]
            args.append('EXTRA_OPTIONS='+' '.join(plusargs))

        self._run_tool('make', args)
