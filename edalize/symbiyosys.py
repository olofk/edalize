import os
import re
import jinja2

from edalize.edatool import Edatool


class Symbiyosys(Edatool):

    _description = '''SymbiYosys backend

SymbiYosys is a wrapper around yosys to make it easier to do formal
verification.

Example snippet in CAPI2 format:

.. code:: yaml

   symbiyosys:
     tasknames:
       # A list of task names to pass to sby. Defaults to empty (in which case
       # sby will run each task in the .sby file)
       - my_proof

The SymbiYosys tool expects a configuration file telling it what to do. This
file includes a list of all the source files, together with various flags which
we'd like to make customizable (we support vlogdefine and vlogparam).

To use the Edalize wrapper, you should include exactly one source file with
file type 'sbyConfigTemplate'. This template file is a Jinja2 template and is
expanded to yield a ``test.sby`` in the build directory.

The sby file format expects a list of input files (twice: each file needs to
appear in a read line at the start of the ``[script]`` section, then again in
the ``[files]`` section). To make this a bit easier, the Edalize backend
supplies several variables and a custom filter.

If you don't need to do anything particularly complicated, start your script
section with something like this:

.. code::

    [script]
    {{"-sv"|gen_reads}}

This will expand to something like:

.. code::

    [script]
    read -sv -Ddefine1=1 -Ddefine2=2 -Isome/include/dir file1.sv
    read -sv -Ddefine1=1 -Ddefine2=2 -Isome/include/dir file2.sv
    chparam -set foo 'bar' -set baz 'qux' my_toplevel


Here, the list of files is the list of files given to Edalize in the first
place. The include directories also come from the file list (calculated by
Edalize's internal fileset tracking). The defines come from ``vlogdefine``
parameters and the chparam command comes from ``vlogparam`` parameters.

Similarly, write a files section like this:

.. code::

    [files]
    {{files}}

which will expand to

.. code::

    [files]
    ../path/to/some/file1.sv
    ../path/to/file2.sv

If you need more control over the read commands at the start of the script
section, there are some variables that can help you.

  - ``{{chparam}}`` expands to the chparam command at the end of gen_reads as
    shown above.

  - ``{{flags}}`` expands to the flags (defines and includes) used for each
    read line.

  - ``{{src_files}}`` expands to a list with the basename of each source file.

  - ``{{top_level}}`` exands to the name of the top-level module.

You can reproduce the example above with something like

.. code::

    [script]
    {% for name in src_files %}
    read -sv {{flags}} {{name}}
    {% endfor %}
    {{chparam}}

    '''

    argtypes = ['vlogdefine', 'vlogparam']

    tool_options = {
        'lists': {
            # A list of tasks to run from the .sby file. Passed on the sby
            # command line.
            'tasknames': 'String'
        }
    }

    def __init__(self, edam=None, work_root=None, eda_api=None):
        super(Symbiyosys, self).__init__(edam, work_root, eda_api)

        # Register Jinja filters
        self.jinja_env.filters["gen_reads"] = self._gen_reads

        # The list of RTL paths in the fileset (populated at configure time by
        # _get_file_names)
        self.rtl_paths = None

        # The list of include directories in the fileset (populated at
        # configure time by _get_file_names)
        self.incdirs = None

        # The name of the interpolated .sby file that we create in the work
        # root
        self.sby_name = 'test.sby'

    @staticmethod
    def get_doc(api_ver):
        if api_ver == 0:
            return {'description':
                    'SymbiYosys formal verification wrapper for Yosys',
                    'lists': [
                        {
                            'name': 'tasknames',
                            'type': 'String',
                            'desc': ("A list of the .sby file's tasks to run. "
                                     "Passed on the sby command line.")
                        }
                    ]}

    def _get_file_names(self):
        '''Read the fileset to get our file names'''
        assert self.rtl_paths is None

        src_files, self.incdirs = self._get_fileset_files()
        self.rtl_paths = []
        bn_to_path = {}
        sby_names = []

        # RTL files have types verilogSource or systemVerilogSource*. We
        # presumably want some of them. The .sby file has type sbyConfig: we
        # want exactly one of them.
        ft_re = re.compile(r'(:?systemV|v)erilogSource')
        for file_obj in src_files:
            if ft_re.match(file_obj.file_type):
                self.rtl_paths.append(file_obj.name)

                # Check that basenames are unique (otherwise sby's behaviour of
                # copying everything into the same directory isn't going to
                # work).
                basename = os.path.basename(file_obj.name)
                if basename in bn_to_path:
                    raise RuntimeError("More than one RTL file with the same"
                                       "basename: {!r} and {!r}."
                                       .format(bn_to_path[basename],
                                               file_obj.name))

                bn_to_path[basename] = file_obj.name
                continue

            if file_obj.file_type == 'sbyConfigTemplate':
                sby_names.append(file_obj.name)
                continue

            # Ignore anything else

        if len(sby_names) != 1:
            raise RuntimeError("SymbiYosys expects exactly one file with type "
                               "sbyConfigTemplate (the one called "
                               "something.sby.j2). We have {}."
                               .format(sby_names or "none"))

        return sby_names[0]

    def _get_read_flags(self):
        '''Return a string with the flags that should be passed for each read.

        These are exposed as the {{flags}} variable in Jinja templates.

        '''
        return ' '.join(['-D{}={}'.format(key, self._param_value_str(value))
                         for key, value in self.vlogdefine.items()] +
                        ['-I{}'.format(inc) for inc in self.incdirs])

    def _get_chparam(self):
        '''Return a string for the {{chparam}} variable'''
        if not self.vlogparam:
            return ''

        chparam_lst = ['chparam']
        for key, value in self.vlogparam.items():
            chparam_lst += ['-set', key,
                            self._param_value_str(param_value=value,
                                                  str_quote_style='"')]
        chparam_lst.append(self.toplevel)
        return ' '.join(chparam_lst)

    def _gen_reads(self, value):
        '''Custom jinja filter that generates read lines for each source file.

        We expect it to be used like this:

            {{"-sv"|gen_reads}}

        See the class documentation for more details.

        '''
        base_cmd = 'read {} {} '.format(value, self._get_read_flags())

        lines = []
        for path in self.rtl_paths:
            lines.append(base_cmd + os.path.basename(path))

        chparam = self._get_chparam()
        if chparam:
            lines.append(chparam)

        return '\n'.join(lines)

    def _interpolate_sby(self, src):
        '''Patch a .sby template to read the right paths

        The input file should be a Jinja template. We expect it not to have
        much templating, but the user will probably want to use templating for
        the list of source files (that has to appear twice).

        See the class documentation for details of the templating variables.

        '''
        # This should have been set by _get_file_names by now
        assert self.rtl_paths is not None

        src_path = os.path.join(self.work_root, src)
        dst_path = os.path.join(self.work_root, self.sby_name)

        # Load the source sby file as a Jinja2 template. We load it directly
        # (rather than through self.jinja_env) because it's user-supplied,
        # rather than living somewhere in the Edalize tree.
        with open(src_path) as sf:
            try:
                template = self.jinja_env.from_string(sf.read())
            except jinja2.TemplateError as err:
                raise RuntimeError('Failed to load {!r} '
                                   'as a Jinja2 template: {}.'
                                   .format(src_path, err))

        files = '\n'.join(self.rtl_paths)

        template_ctxt = {
            'chparam': self._get_chparam(),
            'files': files,
            'flags': self._get_read_flags(),
            'src_files': [os.path.basename(p) for p in self.rtl_paths],
            'top_level': self.toplevel
        }

        with open(dst_path, 'w') as df:
            df.write(template.render(template_ctxt))

    def _dump_file_lists(self):
        '''Dump the list of RTL files and incdirs in work_root

        This is useful if you need to run some sort of hook that consumes the
        list of files (to run sv2v in place on them, for example). The list of
        RTL files goes to files.txt and the list of include directories goes to
        incdirs.txt.

        '''
        with open(os.path.join(self.work_root, 'files.txt'), 'w') as handle:
            handle.write('\n'.join(self.rtl_paths) + '\n')
        with open(os.path.join(self.work_root, 'incdirs.txt'), 'w') as handle:
            handle.write('\n'.join(self.incdirs) + '\n')

    def configure_main(self):
        clean_sby_name = self._get_file_names()
        self._interpolate_sby(clean_sby_name)
        self._dump_file_lists()

    def build_main(self):
        pass

    def run_main(self):
        tasknames = self.tool_options.get('tasknames', [])
        if not isinstance(tasknames, list):
            raise RuntimeError('"tasknames" tool option should be '
                               'a list of strings. Got {!r}.'
                               .format(tasknames))

        self._run_tool('sby', ['-d', 'build', self.sby_name] + tasknames)
