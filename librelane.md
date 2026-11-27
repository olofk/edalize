# LibreLane backend for Edalize

## Status

LibreLane support is implemented as the `librelane` flow in the flow API. It
has unit tests and has been run end to end on LibreLane's `spm` example, see
[End-to-end test](#end-to-end-test).

- `edalize/flows/librelane.py`: the flow
- `edalize/tools/librelane.py`: the tool node the flow runs
- `tests/test_flow_librelane.py`, with golden files in `tests/flows/librelane/`

Facts about LibreLane below were checked against the LibreLane 3.0.17 source,
the latest release on PyPI as of 2026-11-11.

## Background

LibreLane is the FOSSi Foundation continuation of OpenLane 2, which Efabless
developed before shutting down. Version 3.0 was announced in March 2026. It is
Apache 2.0 licensed.

Edalize already has `edalize/openlane.py` in the legacy tool API. It targets
OpenLane 1, rendering a Tcl `config.tcl` and calling `flow.tcl`. LibreLane has
a different CLI and config format, so that backend can't be reused. It is left
untouched.

## How LibreLane is driven

### Configuration

- Config files can be JSON, YAML or Tcl. Edalize writes JSON.
- Several config files can be passed. They are layered in order, and the design
  directory is the directory of the last one unless `--design-dir` is given.
- `dir::<path>` resolves to `$DESIGN_DIR/<path>` and is then made absolute.
  Using it on an absolute path therefore gives a wrong path.
- Other prefixes: `pdk_dir::` (relative to `$PDK_ROOT/$PDK`), `refg::` (glob),
  `ref::` and `expr::`.
- `-c KEY=VALUE` overrides are applied after all config files. Values are
  strings that LibreLane parses permissively.
- A `meta` object in the config can select the flow (`"meta": {"flow": "Classic"}`)
  and substitute steps (`substituting_steps`).

### Synthesis inputs

- Every file in `VERILOG_FILES` is read with `read_verilog -sv`, so plain
  Verilog and the SystemVerilog subset Yosys supports both work.
- `VERILOG_DEFINES` entries become `-D<define>`.
- `SYNTH_PARAMETERS` entries (`name=value`) become
  `chparam -set <name> <value> <top>`. Yosys reads the value as a Verilog
  constant, so strings need double quotes.
- `USE_SLANG` switches to the yosys-slang frontend for better SystemVerilog
  support.
- `VHDL_FILES` is read through the GHDL plugin by the `VHDLClassic` flow. If
  `VERILOG_FILES` is also set, the VHDL files are ignored.

### CLI

| Flag | Purpose |
|------|---------|
| `-f/--flow` | Flow name, e.g. `Classic` (default), `Chip`, `VHDLClassic` |
| `-p/--pdk`, `-s/--scl`, `--pad` | PDK, standard cell library, pad library |
| `--pdk-root`, `--manual-pdk` | Use a local PDK instead of a ciel/volare download |
| `--run-tag`, `--overwrite`, `--last-run` | Run directory naming and reuse |
| `-F/--from`, `-T/--to`, `--only`, `-S/--skip` | Partial runs |
| `-c/--override-config KEY=VALUE` | Override config variables |
| `--dockerized` | Run the rest of the command line in the LibreLane container |
| `-m/--docker-mount DIR` | Extra container mount, must come before `--dockerized` |
| `--save-views-to DIR` | Copy final views to a directory |

`--dockerized` forwards only the arguments after it into the container. The
container mounts the home directory, the current directory and the PDK root.

Exit codes are 0 on success, 1 on config or CLI errors and 2 when a flow step
fails, so a failing run fails the Makefile rule.

### Run directory

Each run goes to `runs/<tag>/` in the design directory. Reusing a tag resumes
the existing run unless `--overwrite` is given, which deletes it first. Final
views are copied to `runs/<tag>/final/<format>/`, named after `DESIGN_NAME`
(e.g. `final/gds/<DESIGN_NAME>.gds`, `final/pnl/<DESIGN_NAME>.pnl.v`), next to
`metrics.json` and `metrics.csv`.

## Implementation

### Flow and tool node

Edalize flows are graphs of nodes, and each node is a class in
`edalize/tools/`. The `Librelane` flow subclasses `Generic` with the tool fixed
to `librelane`, the same pattern as the Efinity flow. The `frontends` flow
option works as usual, e.g. `frontends: [sv2v]`.

### Generated config.json

| EDAM | LibreLane variable |
|------|--------------------|
| `toplevel` | `DESIGN_NAME` |
| `verilogSource*`, `systemVerilogSource*` | `VERILOG_FILES` |
| `vhdlSource*` | `VHDL_FILES` |
| include files (`is_include_file`) | `VERILOG_INCLUDE_DIRS` |
| `vlogdefine` | `VERILOG_DEFINES` (`NAME=value`) |
| `vlogparam` | `SYNTH_PARAMETERS` (`name=value`, strings quoted) |
| `SDC` file | `PNR_SDC_FILE` and `SIGNOFF_SDC_FILE` |
| `librelane_config` entries | Written last, overriding generated variables |

Relative paths get the `dir::` prefix. `config.json` is written to `work_root`,
which makes `work_root` the design directory, and EDAM paths are relative to
`work_root`. Absolute paths are written unchanged. Other file types are
ignored.

### Command

```
librelane [librelane_options] --run-tag edalize --overwrite [--pdk P] [--scl S] [--flow F] config.json
```

The Makefile target is `runs/edalize/final/gds/<toplevel>.gds`. It depends on
`config.json` and every file passed to LibreLane. `config.json` is only
rewritten when its content changes, so make reruns LibreLane only when an input
changed.

### Options

| Option | Type | Purpose |
|--------|------|---------|
| `pdk` | str | `--pdk`, e.g. `sky130A`, `gf180mcuD`, `ihp-sg13g2` |
| `scl` | str | `--scl` |
| `librelane_flow` | str | `--flow`, e.g. `Classic`, `VHDLClassic`, `Chip` |
| `librelane_config` | list of str | Extra variables as `KEY=VALUE` |
| `librelane_options` | list of str | Extra CLI options, placed first |

The usual Edaflow options (`frontends`, `build_runner`, `flow_make_options`)
also apply. `librelane_config` values are parsed as JSON when possible, so
`CLOCK_PERIOD=20` gives a number and `DIE_AREA=[0, 0, 100, 100]` a list.
Anything that isn't valid JSON, such as `CLOCK_PORT=clk`, is kept as a string.

### Usage from FuseSoC

```yaml
targets:
  asic:
    flow: librelane
    flow_options:
      pdk: sky130A
      librelane_config:
        - CLOCK_PORT=clk
        - CLOCK_PERIOD=20
    toplevel: my_top
```

FuseSoC also exposes the options on its command line, e.g. `--pdk gf180mcuD`.

## Design decisions

1. A dedicated flow in the flow API. The legacy tool API is going to be
   deprecated.

2. The `librelane` CLI is used instead of the Python API (`Flow.factory.get`,
   `Config.load`). The CLI fits Edalize's Makefile model, keeps
   `EDALIZE_LAUNCHER`, build runners and `--dockerized` working, and doesn't
   make LibreLane a dependency of Edalize. See
   [Alternative: LibreLane's Python API](#alternative-librelanes-python-api).

3. Extra config is a list of `KEY=VALUE` strings. FuseSoC builds a command-line
   argument for every flow and tool option from a type table with only `bool`,
   `file`, `int`, `str` and `real`, so a dict option would make `fusesoc run`
   fail. The entries are written into `config.json` instead of being passed as
   `-c`, which keeps the full configuration in one file and avoids shell
   quoting in the Makefile.

   A user-supplied LibreLane config file in the fileset was considered and
   dropped. LibreLane takes the design directory from the last config file, so
   either the paths Edalize generates or the `dir::` paths in the user's file
   would resolve against the wrong directory.

4. A fixed run tag (`edalize`) with `--overwrite` gives make a stable target
   path. The cost is that LibreLane's run history is not kept.

5. `librelane_options` go directly after `librelane` so that `--dockerized`
   (and `--docker-mount` before it) works.

6. Only one SDC file is accepted, and it is used for both PnR and signoff. Two
   or more raise an error.

7. The output EDAM is not extended with the GDS or netlist. The flow has no
   downstream nodes, so nothing would consume them yet.

## Alternative: LibreLane's Python API

The code itself would not be hard to write. Running a flow through the API
takes a few lines, and the Edalize side would be roughly 50 to 100 lines plus
tests that use a fake `librelane` module. The cost is in what an in-process
run loses compared to the CLI. An optional dependency suits configure-time
validation well and running the flow less well.

Facts in this section were checked against the LibreLane 3.0.17 source.

### The API

```python
from librelane.flows import Flow

FlowClass = Flow.factory.get("Classic")
flow = FlowClass(config, design_dir=work_root, pdk="sky130A", scl=None, pdk_root=None)
state = flow.start(tag="edalize", overwrite=True)
```

`config` can be a dict, so no `config.json` would be needed. The constructor
loads and validates the configuration through `Config.load` and raises
`InvalidConfig`, a `ValueError` carrying `errors` and `warnings` lists.
Constructing the flow has no other side effects. `start()` runs the flow and
returns the final `State`. It raises `FlowError` when a step fails and
`FlowException`, a subclass, on unexpected errors.

### LibreLane as an optional dependency

It would be an extra in `pyproject.toml`:

```toml
[project.optional-dependencies]
librelane = ["librelane>=3,<4; python_version >= '3.10'"]
```

Things to know before adding it:

- LibreLane needs Python 3.10 or later. Edalize supports 3.9, hence the marker.
- It pulls in ciel, click (pinned below 8.3), cloup, httpx, klayout (the Python
  wheel), lln-libparse, lxml, psutil, pyyaml, rapidfuzz, rich, semver and
  yamlcore. The click upper bound can conflict with other packages installed
  next to FuseSoC.
- Importing `librelane` imports every installed `librelane_plugin_*` and
  `openlane_plugin_*` package and sets up its own `__librelane__` logger with
  rich handlers. The root logger is left alone.
- The pip package only contains the Python code. Yosys, OpenROAD, Magic,
  KLayout and Netgen still have to be on `PATH` in the process that runs the
  flow, which usually means LibreLane's Nix environment.

### Option A: run the flow in-process

The flow would override `build()` (the Vivado flow already does) and call the
API instead of make. Compared to the CLI this loses:

- `--dockerized`. Container support exists only in the CLI, so the EDA tools
  must be installed on the host and FuseSoC itself has to run inside
  LibreLane's environment.
- PDK download. Fetching with ciel happens in the CLI layer
  (`librelane/flows/cli.py`). The API only looks for an existing PDK under
  `pdk_root` (ciel's home directory by default) and fails with "The PDK
  <pdk> was not found." Edalize would have to call ciel itself or require
  pre-fetched PDKs.
- The Makefile model. Build runners, `flow_make_options`, `EDALIZE_LAUNCHER`,
  incremental rebuilds and the `pre_build`/`post_build` hooks all go through
  the generated Makefile. `build()` would have to run the hook targets around
  the API call and do its own up-to-date check.

In return it gives Python exceptions instead of exit codes and the final
`State` in memory. Edalize has no use for the state today, and the same
metrics are in `final/metrics.json`.

Choosing between API and CLI based on whether `import librelane` succeeds
means the same core runs differently on two machines. Failures from missing
tools or PDKs would then only show up where the package happens to be
installed. If in-process runs are wanted, an explicit option such as
`librelane_api: true` that errors when the package is missing is easier to
support.

### Option B: validate the configuration at configure time

The flow keeps running the CLI. When `librelane` is importable, `configure()`
also constructs the flow object without calling `start()`:

```python
try:
    from librelane.flows import Flow
except ImportError:
    Flow = None  # LibreLane not installed, skip validation

if Flow:
    Flow.factory.get(flow_name)(config, design_dir=work_root, pdk=pdk, scl=scl)
```

The constructor runs `Config.load` with the flow's full variable list. That
catches unknown or misspelled variables in `librelane_config`, wrong value
types and missing input files at configure time, instead of partway through a
long run. Execution is unchanged, so nothing listed under option A is lost.
This is where the optional dependency fits: without the package, the only
difference is fewer early checks.

The catch is the PDK. `Config.load` reads the PDK configuration and fails with
"The PDK <pdk> was not found." until the PDK has been fetched, which with the
CLI's default ciel fetching is always the case before the first run.
Validation should check for the PDK directory first and be skipped when it is
missing. Estimated size is 20 to 30 lines plus a test.

### Recommendation

Keep the CLI for running the flow. If we want something from the API, option B
is cheap and suits an optional dependency. Option A is worth revisiting only if
Edalize needs something the CLI can't do. Custom flows mostly don't qualify,
since the config's `meta.flow` accepts a list of step IDs and the CLI loads
plugins as well.

## Known limitations

- VHDL designs need `librelane_flow: VHDLClassic` set by hand. VHDL generics
  are not mapped, since the flow only takes `vlogdefine` and `vlogparam`.
- Files tagged `simulation` are passed to LibreLane. The Yosys tool filters
  them out.
- Paths inside `librelane_config` values, such as
  `IO_PIN_ORDER_CFG=dir::pin_order.cfg`, resolve against the build directory
  instead of the core directory. Use absolute paths there.
- There are no file types for LibreLane inputs like pin order configs or macro
  LEF/GDS. They have to go through `librelane_config`.
- With `--dockerized`, sources outside the home directory, the build directory
  and the PDK root need `--docker-mount <dir>` before `--dockerized` in
  `librelane_options`.
- Without a terminal, `--dockerized` fails with "cannot attach stdin to a
  TTY-enabled container because stdin is not a terminal". Put
  `--docker-no-tty` before `--dockerized` for non-interactive runs such as CI.
- The Chip flow's pad library has no dedicated option. Pass `--pad` through
  `librelane_options`.

## Testing

`tests/test_flow_librelane.py` covers:

- all options with the shared test file set (Makefile and `config.json`
  golden files in `tests/flows/librelane/options/`)
- the minimal case, with one relative and one absolute source path
  (`tests/flows/librelane/minimal/`)
- the error for more than one SDC file
- the error for a `librelane_config` entry without `=`

Regenerate the golden files with
`GOLDEN_RUN=1 pytest tests/test_flow_librelane.py`.

Two environment issues showed up during development, neither caused by this
change. The black 22.3.0 hook in `.pre-commit-config.yaml` crashes on Python
3.14, so formatting was checked with
`uvx --python /usr/bin/python3.12 black==22.3.0`. `tests/test_reporting.py`
needs `pandas`.

## End-to-end test

LibreLane's `spm` example was run through a FuseSoC core on 2026-11-11, using
LibreLane 3.0.17 from PyPI with `--dockerized` (image
`ghcr.io/librelane/librelane:3.0.17`). ciel fetched sky130A to `~/.ciel` on
the first run. The flow completed with no DRC or LVS errors and positive setup
and hold slack, and the GDS was written to `runs/edalize/final/gds/spm.gds` as
expected. Running `make` again, or after `fusesoc run --setup`, did nothing.

The core, with `src/` and `pin_order.cfg` copied from
`librelane/examples/spm` in the installed package:

```yaml
CAPI=2:
name: ::spm:0

filesets:
  rtl:
    files:
      - src/spm.v
      - src/impl.sdc: {file_type: SDC}
    file_type: verilogSource

targets:
  asic:
    filesets: [rtl]
    flow: librelane
    flow_options:
      pdk: sky130A
      librelane_options: [--docker-no-tty, --docker-mount, /path/to/spm, --dockerized]
      librelane_config:
        - CLOCK_PORT=clk
        - CLOCK_PERIOD=10
        - FP_CORE_UTIL=45
        - PDN_VOFFSET=5
        - PDN_HOFFSET=5
        - PDN_VWIDTH=2
        - PDN_HWIDTH=2
        - PDN_VPITCH=30
        - PDN_HPITCH=30
        - PDN_SKIPTRIM=true
        - IO_PIN_ORDER_CFG=/path/to/spm/pin_order.cfg
    toplevel: spm
```

The example has separate implementation and signoff SDC files. Only
`impl.sdc` was used, since the flow takes one SDC file. The core lived outside
the home directory, so the pin order file needed `--docker-mount`.

An edalize clone without git tags gets a version below 0.4.1 from
setuptools_scm, which FuseSoC rejects. Setting
`SETUPTOOLS_SCM_PRETEND_VERSION_FOR_EDALIZE` during install works around it.

## Next steps

1. Decide whether to filter `simulation` files and select `VHDLClassic`
   automatically for VHDL-only designs.
2. Open a PR upstream.

## Sources

- [LibreLane documentation](https://librelane.readthedocs.io/en/latest/)
- [Design configuration files](https://librelane.readthedocs.io/en/latest/reference/configuration.html)
- [Built-in flows](https://librelane.readthedocs.io/en/latest/reference/flows.html)
- [Universal flow configuration variables](https://librelane.readthedocs.io/en/latest/reference/common_flow_vars.html)
- [Newcomers tutorial](https://librelane.readthedocs.io/en/latest/getting_started/newcomers/index.html)
- [Config API reference](https://librelane.readthedocs.io/en/latest/reference/api/config/index.html)
- [LibreLane source](https://github.com/librelane/librelane)
- [LibreLane 3.0 announcement](https://fossi-foundation.org/librelane/blog/2026-03-25-website_release_3-0)
- [LibreLane on PyPI](https://pypi.org/project/librelane/)
