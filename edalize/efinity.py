# Copyright edalize contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
import platform
import sys
import re
import subprocess

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Efinity(Edatool):
    """
    Efinity Backend.
    """

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    # Define the templates for project
    prj_template = "newproj_tmpl.xml.j2"

    efx_env_code =  'import os; import sys;' + \
                    'efinity_home = os.getenv("EFINITY_HOME");' + \
                    'os.environ["EFXPT_HOME"]        = efinity_home + "/pt";' +  \
                    'os.environ["EFXPGM_HOME"]       = efinity_home + "/pgm";' +  \
                    'os.environ["EFXDBG_HOME"]       = efinity_home + "/debugger";' +  \
                    'os.environ["EFXIPM_HOME"]       = efinity_home + "/ipm";' +  \
                    'os.environ["EFXIPMGR_HOME"]     = efinity_home + "/ipm/bin/ip_manager";' +  \
                    'os.environ["EFXIPPKG_HOME"]     = efinity_home + "/ipm/bin/ip_packager";' + \
                    'os.environ["EFXSVF_HOME"]       = efinity_home + "/debugger/svf_player";' + \
                    'os.environ["QT_LOGGING_CONF"]   = efinity_home + "/bin/lc.ini";' + \
                    'os.environ["QT_PLUGIN_PATH"]    = efinity_home + "/lib/plugins";' + \
                    'os.environ["PYTHONNOUSERSITE"]  = "1";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFINITY_HOME"] + "/bin";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFINITY_HOME"] + "/scripts";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFXPT_HOME"] + "/bin";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFXPGM_HOME"] + "/bin";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFXDBG_HOME"] + "/bin";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFXSVF_HOME"] + "/bin";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFXIPM_HOME"] + "/bin";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFXIPMGR_HOME"];' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFXIPPKG_HOME"];' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFINITY_HOME"] + "/python38";' + \
                    'os.environ["PATH"] += os.pathsep + os.environ["EFINITY_HOME"] + "/python38/bin";' + \
                    'sys.path.append(os.getenv("EFXPT_HOME") + "/bin");'

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "The Efinity backend executes Efinity to build systems and program the FPGA",
                "members": [
                    {
                        "name": "family",
                        "type": "String",
                        "desc": "Accepted is Trion and Titanium (default)",
                    },
                    {
                        "name": "part",
                        "type": "String",
                        "desc": "FPGA part number (e.g. Ti180M484)",
                    },
                    {
                        "name": "timing",
                        "type": "String",
                        "desc": "Speed grade (e.g. C4)",
                    },
                ],
            }

    def configure_main(self):
        '''
        Create required files to make an Efinix build. Two files required:
        - XML project file
        - XML file with IO and hard blocks definitions (only done if an ISF file is included)
        '''
        self.efinity_home = os.getenv('EFINITY_HOME')
        if self.efinity_home == None:
            raise Exception("The environment variable EFINITY_HOME is not set.")

        if sys.platform == "win32" or sys.platform == "cygwin":
            self.efinity_python = self.efinity_home + "/python38/bin/python"
        else:
            self.efinity_python = self.efinity_home + "/bin/python3"

        for i in ["family", "part", "timing"]:
            if not i in self.tool_options:
                raise RuntimeError("Missing required option '{}'".format(i))
        family = self.tool_options.get("family")
        part   = self.tool_options.get("part")
        timing = self.tool_options.get("timing")

        (src_files, incdirs) = self._get_fileset_files()
        design_files = []
        sv_files     = []
        constr_files = []
        isf_files    = []
        for f in src_files:
            ff = f.name
            if (ff.endswith(".vhdl") or ff.endswith(".vhd") or ff.endswith(".v")):
                design_files.append(ff)
            elif (ff.endswith(".sv") or ff.endswith(".svh")):
                sv_files.append(ff)
            elif ff.endswith(".sdc"):
                constr_files.append(ff)
            elif ff.endswith(".isf"):
                isf_files.append(ff)

        template_vars = {
            "name"        : self.name,
            "design_files": design_files,
            "sv_files"    : sv_files,
            "constr_files": constr_files,
            "tool_options": self.tool_options,
            "toplevel"    : self.toplevel,
            "vlogparam"   : self.vlogparam,
            "vlogdefine"  : self.vlogdefine,
            "generic"     : self.generic
        }

        logger.info("--------------------------------------------------------------------------")
        logger.info("Creating the XML project file for Efinix tool")
        logger.info("--------------------------------------------------------------------------")

        # Render XML project file
        self.render_template(self.prj_template, self.name + '.xml', template_vars)
        print("XML project file has been generated at " + self.work_root + '/' + self.name + '.xml')
        self.prj_file = self.work_root + '/' + self.name + '.xml'

        workdir = self.work_root
        if sys.platform == "win32" or sys.platform == "cygwin":
            # We have to convert the path using the "C:" format for the ISF step to work
            check = ["/c/", "/C/", "\\c\\", "\\C\\"]
            for elem in check:
                if workdir.startswith(elem):
                    workdir = workdir.replace(elem, "C:/")

        if isf_files:
            if len(isf_files) != 1:
                raise RuntimeError("The Efinity backend only supports a single ISF file.")

             # Create XML file with IO and hard blocks definitions
            efx_isf_code =  'from api_service.design import DesignAPI;' + \
                            'from api_service.device import DeviceAPI;' + \
                            'import api_service.excp.design_excp as APIExcp;' + \
                            'print("INFO: --------------------------------------------------------------------------");' + \
                            'print("INFO: Creating the XML constraint file for Efinix tool");' + \
                            'print("INFO: --------------------------------------------------------------------------");' + \
                            'is_verbose = False;' + \
                            'design = DesignAPI(is_verbose);' + \
                            'device = DeviceAPI(is_verbose);' + \
                            'design.create("' + self.name + '","' + part + '","' + workdir + '");' + \
                            'design.import_design("'+ isf_files[0] + '");' + \
                            'design.generate(enable_bitstream=False);' + \
                            'design.save_as("' + workdir + '/' + self.name + '.peri.xml");' + \
                            'print("XML ISF file has been generated at ' + self.work_root + '/' + self.name + '.peri.xml");'

            self.isf_file = self.work_root + "/" + self.name + ".peri.xml"

            subprocess.run([self.efinity_python, "-c", self.efx_env_code + efx_isf_code],
                           cwd=self.work_root, check=True)

    def run_tool(self, cmd, args=[], env='', quiet=False):
        '''
        We have to modify the run_tool function from EdaTool in order to pass an environment to
        the subprocess call
        '''
        logger.debug("Running " + cmd)
        logger.debug("args  : " + " ".join(args))

        capture_output = quiet and not (self.verbose or self.stdout or self.stderr)
        try:
            cp = subprocess.run(
                [cmd] + args,
                env=env,
                cwd=self.work_root,
                stdin=subprocess.PIPE,
                stdout=self.stdout,
                stderr=self.stderr,
                capture_output=capture_output,
                check=True,
            )
        except FileNotFoundError:
            _s = "Command '{}' not found. Make sure it is in $PATH".format(cmd)
            raise RuntimeError(_s)
        except subprocess.CalledProcessError as e:
            _s = "'{}' exited with an error: {}".format(e.cmd, e.returncode)
            logger.debug(_s)

            if e.stdout:
                logger.info(e.stdout.decode())
            if e.stderr:
                logger.error(e.stderr.decode())
                logger.debug("=== STDERR ===")
                logger.debug(e.stderr)

            raise RuntimeError(_s)
        return cp.returncode, cp.stdout, cp.stderr

    def build_main(self):
        '''
        "--flow compile" performs synthesis, place and route, and generates a bitstream hex file
        '''
        logger.info("Building")
        logger.info("--------------------------------------------------------------------------")
        logger.info("Running the Efinix flow to synthetize, P&R, generate bitstream")
        logger.info("--------------------------------------------------------------------------")

        efx_env = os.environ.copy()
        efx_env["EFXPT_HOME"]    = efx_env["EFINITY_HOME"]  + "/pt"
        efx_env["EFXPGM_HOME"]   = efx_env["EFINITY_HOME"]  + "/pgm"
        efx_env["EFXDBG_HOME"]   = efx_env["EFINITY_HOME"]  + "/debugger"
        efx_env["EFXIPM_HOME"]   = efx_env["EFINITY_HOME"]  + "/ipm"
        efx_env["EFXIPMGR_HOME"] = efx_env["EFINITY_HOME"]  + "/ipm/bin/ip_manager"
        efx_env["EFXIPPKG_HOME"] = efx_env["EFINITY_HOME"]  + "/ipm/bin/ip_packager"
        efx_env["EFXSVF_HOME"]   = efx_env["EFINITY_HOME"]  + "/debugger/svf_player"
        efx_env["PATH"]          = efx_env["EFINITY_HOME"]  + "/bin:" + \
                                   efx_env["EFINITY_HOME"]  + "/scripts:" + \
                                   efx_env["EFXPT_HOME"]    + "/bin:" + \
                                   efx_env["EFXPGM_HOME"]   + "/bin:" + \
                                   efx_env["EFXDBG_HOME"]   + "/bin:" + \
                                   efx_env["EFXSVF_HOME"]   + "/bin:" + \
                                   efx_env["EFXIPM_HOME"]   + "/bin:" + \
                                   efx_env["EFXIPMGR_HOME"] + ":" + \
                                   efx_env["EFXIPPKG_HOME"] + ":" + \
                                   efx_env["EFINITY_HOME"]  + "/python38/bin:" + \
                                   efx_env["PATH"]

        efx_run        = self.efinity_home + "/scripts/efx_run.py"
        args           = [efx_run, "--prj", self.name + '.xml', "--work_dir", self.work_root, "--flow", "compile"]
        self.run_tool(self.efinity_python, args, env=efx_env, quiet=False)

    def run_main(self):
        '''
        Program the FPGA.
        '''
        pass
