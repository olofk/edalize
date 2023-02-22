import os
import logging

from edalize.edatool import Edatool

logger = logging.getLogger(__name__)

SANDPIPER_CHECK = """
ifeq (, $(shell which sandpiper-saas))
$(error "No Sandpiper-saas installation in $(PATH). Do pip install sandpiper-saas")
endif

"""
MAKEFILE_TEMPLATE = """

BUILD_FILES := {build_files}
RM := rm -r
all: tlv2v
	@echo "Finished"

tlv2v:
	sandpiper-saas -i $(INPUTFILE) -o $(OUTPUTFILE) $(OUTPUTDIR) $(INCLUDES) $(SANDPIPER_SAAS_OPTIONS) $(SANDPIPER_JAR_OPTIONS)   
clean:
	$(RM) $(BUILD_FILES)

"""


class Sandpipersaas(Edatool):

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "SandPiper SaaS Edition runs Redwood EDA's SandPiper™ TL-Verilog compiler as a microservice in the cloud to support low-overhead and zero-cost open-source development using commercial-grade capabilities. ",
                "members": [
                    # {"name": "timescale", "type": "String", "desc": "Default timescale"}
                ],
                "lists": [
                    {
                        "name": "sandpiper_saas",
                        "type": "String",
                        "desc": "Additional options for sandpiper-saas",
                    },
                    {
                        "name": "sandpiper_jar",
                        "type": "String",
                        "desc": "Additional options for sandpiper_jar",
                    },
                    {
                        "name": "output_file",
                        "type": "String",
                        "desc": "Name of the output Verilog/System Verilog file (Must contain .v or .sv",
                    },
                    {
                        "name": "output_dir",
                        "type": "String",
                        "desc": "Optional: Path to the output directory",
                    },
                    {
                        "name": "endpoint",
                        "type": "String",
                        "desc": "Compile service endpoint",
                    },
                    {
                        "name": "includes",
                        "type": "String",
                        "desc": "List of include files to be used during compilation",
                    },
                ],
            }

    def configure_main(self):

        if len(self.files) > 1:
            raise RuntimeError("Only 1 TL-V file is allowed")

        if self.files[0].get("file_type").lower() != "tlverilogsource":
            raise RuntimeError("Expected file type: TLVerilogSource")

        with open(os.path.join(self.work_root, "Makefile"), "w") as f:
            print(self.tool_options)
            print(self.files)
            f.write(SANDPIPER_CHECK)
            f.write(
                "SANDPIPER_SAAS_OPTIONS := {}\n".format(
                    " ".join(self.tool_options.get("sandpiper_saas", []))
                )
            )
            f.write(
                "SANDPIPER_JAR_OPTIONS := {}\n".format(
                    " ".join(self.tool_options.get("sandpiper_jar", []))
                )
            )
            f.write(
                "OUTPUTFILE :=  {}\n".format((self.tool_options.get("output_file", "")))
            )
            f.write("INPUTFILE := {}\n".format((self.files[0].get("name"))))
            if self.tool_options.get("output_dir", " ") != " ":
                f.write(
                    "OUTPUTDIR :=  --outdir {}\n".format(
                        (self.tool_options.get("output_dir", " "))
                    )
                )
            else:
                f.write(
                    "OUTPUTDIR :=  \n".format(
                        (self.tool_options.get("output_dir", " "))
                    )
                )

            if self.tool_options.get("includes", []) != []:
                f.write(
                    "INCLUDES := -f {}\n".format(
                        " ".join(self.tool_options.get("includes", []))
                    )
                )
            else:
                f.write("INCLUDES := \n")

            if self.tool_options.get("endpoint", " ") != " ":
                f.write(
                    "ENDPOINT := --endpoint {}\n".format(
                        (self.tool_options.get("endpoint", " "))
                    )
                )
            else:
                f.write("ENDPOINT := \n")

            f.write(MAKEFILE_TEMPLATE.format(build_files=self.work_root))

    def run_main(self):
        self._run_tool("make")
