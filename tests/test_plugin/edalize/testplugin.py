import logging
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


class Testplugin(Edatool):
    @classmethod
    def get_doc(cls, api_ver):
        if api_ver == 0:
            return {
                "description": "Test legacy backend plugin",
                "members": [
                    {
                        "name": "member",
                        "type": "String",
                        "desc": "Example member option",
                    },
                ],
            }

    argtypes = ["vlogdefine", "vlogparam", "generic"]

    def configure_main(self):
        """
        Configuration is the first phase of the build.

        This writes the project files. It first collects all
        sources, IPs and constraints and then writes them to the tool-specific
        project files along with the build steps.
        """

        logger.info("Configure done")

    def build_main(self):
        logger.info("Build done")

    def run_main(self):
        logger.info("Run done")
