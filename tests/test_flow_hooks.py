from .edalize_common import FILES, param_gen
from .edalize_flow_common import get_flow


def test_hook_env(tmp_path):
    edam = {
        "name": "design",
        "files": FILES,
        "parameters": param_gen(["plusarg", "vlogdefine", "vlogparam"]),
        "flow_options": {"tool": "icarus"},
        "toplevel": "top_module",
        "hooks": {
            "pre_build": [
                {
                    "name": "sample_pre_build",
                    "cmd": ["echo", "hello"],
                    "env": {"FOO": "bar"},
                }
            ]
        },
    }

    flow = get_flow("sim")(edam, tmp_path)
    flow.configure()

    makefile = (tmp_path / "Makefile").read_text()
    assert "env FOO=bar echo hello" in makefile
