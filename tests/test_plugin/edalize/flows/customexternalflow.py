from edalize.flows.edaflow import Edaflow


class Customexternalflow(Edaflow):

    argtypes = ["plusarg", "vlogdefine", "vlogparam"]

    FLOW_OPTIONS = {}

    def configure(self):
        print("Configuring custom flow")

    def build(self):
        print("Building with custom flow")

    def run(self, args):
        print("Running custom flow")
