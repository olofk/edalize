class EdaCommands(object):
    class Command(object):
        def __init__(self, command, targets, depends, order_only_deps=[], variables=[]):
            self.command = command
            self.targets = targets
            self.depends = depends
            self.order_only_deps = order_only_deps
            self.variables = variables

    def __init__(self):
        self.commands = []
        self.vars = []
        self.header = "#Auto generated by Edalize\n\n"

    def add(self, command, targets, depends, order_only_deps=[], variables=[]):
        self.commands.append(
            self.Command(command, targets, depends, order_only_deps, variables)
        )

    def add_var(self, var):
        self.vars.append(var)

    # Allow for portability between the main platforms
    def find_env_var_command(self):
        from sys import platform

        if platform == "linux" or platform == "linux2" or platform == "darwin":
            return "export"
        elif platform == "win32":
            return "set"
        return ""

    # Simplify the creation of flow environmental variables in the Makefile
    def add_env_var(self, key, value):
        self.vars.append(f"{self.find_env_var_command()} {key}={value}")

    def set_default_target(self, target):
        self.default_target = target

    def write(self, outfile):
        with open(outfile, "w") as f:
            f.write(self.header)
            for v in self.vars:
                f.write(v + "\n")
            if self.vars:
                f.write("\n\n")
            if not self.default_target:
                raise RuntimeError("Internal Edalize error. Missing default target")

            f.write(f"all: {self.default_target}\n")

            for c in self.commands:
                f.write(f"\n{' '.join(c.targets)}:")
                for d in c.depends:
                    f.write(" " + d)
                if c.order_only_deps:
                    f.write(" |")
                    for d in c.order_only_deps:
                        f.write(" " + d)

                f.write("\n")

                env_prefix = ""
                if c.variables:
                    var_list = []
                    for key in c.variables.keys():
                        var_list += f"{key}={c.variables.get(key)}"
                    env_prefix = f"env {' '.join(var_list)}"

                if c.command:
                    f.write(
                        f"\t$(EDALIZE_LAUNCHER) {env_prefix}{' '.join(c.command)}\n"
                    )
