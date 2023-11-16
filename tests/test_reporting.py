from pathlib import Path

import pytest
import pandas as pd

from .edalize_common import tests_dir

PANDAS_VERSION = tuple(map(int, pd.__version__.split(".")[:3]))


def check_types(s, allowed=[int, float]):
    """Check data structures use expected types

    The resource and timing reports intentionally use fancier Pandas/NumPy
    types to facilitate analysis. However, in cases like the summary reports
    it seems best to avoid complex data types. The Quartus and Vivado backends
    successfully stick to numeric values. ISE is harder and will probably
    allow additional types such as strings and None
    """

    if isinstance(s, dict):
        for x in s.values():
            check_types(x, allowed)
    else:
        assert any([isinstance(s, a) for a in allowed])


def round_fmax(s, digits=3):
    """Round fmax dictionary keys to ease comparisions

    ISE allows None for Fmax so skip those cases
    """

    result = s

    for k, v in result["fmax"].items():
        if v is not None:
            result["fmax"][k] = round(v, digits)

    return result


def test_missing_dir():
    from edalize.reporting import Reporting

    data_dir = Path(tests_dir + "/test_reporting/data/doesntexist")

    rpt = Reporting.report(str(data_dir))

    assert rpt == {"summary": None, "resources": None, "timing": None}


def test_no_reports(tmp_path):
    from edalize.reporting import Reporting

    rpt = Reporting.report(str(tmp_path))

    assert rpt == {"summary": None, "resources": None, "timing": None}


def test_missing_reports(tmp_path):
    from edalize.reporting import Reporting

    (tmp_path / "top1_resource_report.txt").touch()

    rpt = Reporting.report(str(tmp_path))

    assert rpt == {"summary": None, "resources": None, "timing": None}


def test_extra_reports(tmp_path):
    from edalize.reporting import Reporting

    (tmp_path / "top1_resource_report.txt").touch()
    (tmp_path / "top2_resource_report.txt").touch()
    (tmp_path / "top1_timing_report.txt").touch()

    rpt = Reporting.report(str(tmp_path))

    assert rpt == {"summary": None, "resources": None, "timing": None}


def test_period_to_freq():
    from edalize.reporting import Reporting

    assert Reporting.period_to_freq(10.0) == 100
    assert round(Reporting.period_to_freq(125, "ps", "GHZ")) == 8
    assert Reporting.period_to_freq(None) is None
    assert Reporting.period_to_freq(float("nan")) is None
    assert round(Reporting.period_to_freq("9", "ns"), 4) == round(1 / 9e-3, 4)

    with pytest.raises(ValueError):
        Reporting.period_to_freq(5, "MHz")
        Reporting.period_to_freq("invalid")
        Reporting.period_to_freq(5, "ps", "ns")


@pytest.fixture(scope="module")
def picorv32_cyclone4_data():
    from edalize.quartus_reporting import QuartusReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/quartus-cyclone4")

    rpt = QuartusReporting.report(str(data_dir))

    return rpt


def test_picorv32_quartus_cyclone4_summary(picorv32_cyclone4_data):
    """Check all summary fields"""

    summary = picorv32_cyclone4_data["summary"]

    check_types(summary)

    expected = {
        "lut": 1632,
        "reg": 649,
        "blkmem": 2,
        "dsp": 0,
        "constraint": {"clk": 175.0},
        "fmax": {"clk": 159.95},
    }

    assert summary == expected


def test_picorv32_quartus_cylone4_resources(picorv32_cyclone4_data):
    """Check selected PicoRV32 resources for the Cyclone 4"""

    rpt = picorv32_cyclone4_data["resources"]

    df = rpt["Fitter Resource Usage Summary"].set_index("Resource")

    assert (
        df.loc["Total LABs:  partially or completely used", "Usage"]
        == "283 / 1,395 ( 20 % )"
    )

    df = rpt["Fitter Resource Utilization by Entity"].set_index(
        "Compilation Hierarchy Node"
    )

    assert df.loc["|altsyncram:cpuregs_rtl_0|", "Memory Bits"] == 1024
    assert df.loc["|picorv32", "M9Ks"] == 2
    assert df.loc["|picorv32", "Logic Cells"] == "1632 (1632)"
    assert df.loc["|picorv32", "Dedicated Logic Registers"] == "649 (649)"

    tables = list(rpt.keys())
    assert len(tables) == 31
    assert "Fitter Summary" in tables
    assert "Estimated Delay Added for Hold Timing Details" in tables


def test_picorv32_quartus_cylone4_timing(picorv32_cyclone4_data):
    """Check selected PicoRV32 timing values for the Cyclone 4"""

    rpt = picorv32_cyclone4_data["timing"]

    df = rpt["Clocks"].set_index("Clock Name")
    assert round(df.loc["clk", "Period"], 3) == 5.714

    df = rpt["Slow 1200mV 85C Model Fmax Summary"].set_index("Clock Name")
    assert df.loc["clk", "Fmax"] == "159.95 MHz"


@pytest.fixture(scope="module")
def picorv32_cyclone10_data():
    from edalize.quartus_reporting import QuartusReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/quartus-cyclone10")

    rpt = QuartusReporting.report(str(data_dir))

    return rpt


def test_picorv32_quartus_cyclone10_summary(picorv32_cyclone10_data):
    """Check all summary fields"""

    summary = picorv32_cyclone10_data["summary"]

    check_types(summary)

    expected = {
        "lut": 1137,
        "reg": 761,
        "blkmem": 2,
        "dsp": 0,
        "constraint": {"clk": 175.0},
        "fmax": {"clk": 131.58},
    }

    assert summary == expected


def test_picorv32_quartus_cyclone10_no_header(picorv32_cyclone10_data):
    """Check a table with no header"""

    df = picorv32_cyclone10_data["resources"]["Fitter Summary"].set_index(0)

    assert df.loc["Total block memory bits", 1] == "2,048 / 12,021,760 ( < 1 % )"


def test_picorv32_quartus_cyclone10_resource_by_entity(picorv32_cyclone10_data):
    """Check several values in the "Fitter Resource Utilization by Entity" table"""

    df = picorv32_cyclone10_data["resources"]["Fitter Resource Utilization by Entity"]

    df.set_index("Compilation Hierarchy Node", inplace=True)

    assert df.loc["|", "Combinational ALUTs"] == "1137 (1137)"
    assert df.loc["|", "Dedicated Logic Registers"] == "761 (761)"
    assert df.loc["|", "M20Ks"] == 2


def test_picorv32_quartus_cyclone10_timing(picorv32_cyclone10_data):
    """Check timing tables"""

    timing = picorv32_cyclone10_data["timing"]
    clocks = timing["Clocks"].set_index("Clock Name")
    fmax = timing["Slow 900mV 100C Model Fmax Summary"].set_index("Clock Name")

    assert clocks.loc["clk", "Frequency"] == "175.0 MHz"
    assert fmax.loc["clk", "Fmax"] == "131.58 MHz"


@pytest.fixture(scope="module")
def picorv32_s6_data():
    from edalize.ise_reporting import IseReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/ise-spartan6")

    rpt = IseReporting.report(str(data_dir))

    return rpt


def test_picorv32_ise_spartan6_summary(picorv32_s6_data):
    """Check all summary fields"""

    summary = picorv32_s6_data["summary"]

    check_types(summary, allowed=[int, float, str, type(None)])

    expected = {
        "lut": 1329,
        "reg": 959,
        "blkmem": 2,
        "dsp": 0,
        "constraint": {"clk": "150 MHz"},
        "fmax": {"clk": 91.937},
    }

    assert round_fmax(summary, digits=3) == expected


def test_picorv32_ise_spartan6_multiline(picorv32_s6_data):
    """Check multi-line headings"""
    df = picorv32_s6_data["resources"]["IOB Properties"]

    assert list(df.columns) == [
        "IOB Name",
        "Type",
        "Direction",
        "IO Standard",
        "Diff Term",
        "Drive Strength",
        "Slew Rate",
        "Reg (s)",
        "Resistor",
        "IOB Delay",
    ]


def test_picorv32_ise_spartan6_resources(picorv32_s6_data):
    """Check resource values"""

    rpt = picorv32_s6_data["resources"]

    assert list(sorted(rpt.keys())) == [
        "Control Set Information",
        "IOB Properties",
        "Utilization by Hierarchy",
    ]

    # Check IOB Properties table
    df = rpt["IOB Properties"].set_index("IOB Name")

    # Check Control Set Information table
    df = rpt["Control Set Information"]

    assert (df["Clock Signal"] == "clk_BUFGP").all()
    assert df.shape == (20, 6)

    rst_en = df[
        (df["Reset Signal"] == "dut/resetn_inv")
        & (df["Enable Signal"] == "dut/cpu_state_FSM_FFd2-In21")
    ]

    slc = rst_en["Slice Load Count"]

    assert slc.size == 1
    assert slc.iat[0] == 19

    # Check Utilization by Hierarchy table
    df = rpt["Utilization by Hierarchy"].set_index("Module")

    assert df.loc["+dut", "BRAM/FIFO"] == "2/2"
    assert df.loc["+dut", "LUTs"] == "1158/1158"
    assert df.loc["top/", "Slice Reg"] == "378/959"
    assert df.loc["top/", "Slices*"] == "73/441"
    assert df.loc["+dut", "Slices*"] == "368/368"


def test_picorv32_ise_spartan6_timing(picorv32_s6_data):
    """Check timing values"""

    rpt = picorv32_s6_data["timing"]

    assert rpt["min period"] == 10.877
    assert rpt["max clock"] == 91.937
    assert rpt["constraint"]["clk"] == {
        "timespec": "TS_clk",
        "constraint": "150 MHz",
        "paths": 39892,
        "endpoints": 3774,
        "failing": 632,
        "timing errors": 632,
        "setup errors": 632,
        "hold errors": 0,
        "switching limit errors": 0,
        "min period": 10.877,
    }


@pytest.fixture(scope="module")
def picorv32_artix7_data():
    from edalize.vivado_reporting import VivadoReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/vivado-artix7/impl")

    rpt = VivadoReporting.report(str(data_dir))

    return rpt


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_picorv32_artix7_summary(picorv32_artix7_data):
    """Check all summary fields"""

    summary = picorv32_artix7_data["summary"]

    check_types(summary)

    expected = {
        "lut": 1009,
        "reg": 920,
        "blkmem": 0,
        "dsp": 0,
        "constraint": {"clk": 200},
        "fmax": {"clk": 118.1614},
    }

    assert round_fmax(summary, digits=4) == expected


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_picorv32_artix7_resources(picorv32_artix7_data):
    """Check selected resource report fields"""

    rpt = picorv32_artix7_data["resources"]

    df = rpt["Slice Logic"].set_index("Site Type")
    assert df.at["Slice Registers", "Used"] == 920

    df = rpt["Memory"].set_index("Site Type")
    assert df.at["RAMB18", "Used"] == 0

    df = rpt["DSP"].set_index("Site Type")
    assert df.at["DSPs", "Used"] == 0
    assert df.at["DSPs", "Available"] == 740


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_picorv32_artix7_timing(picorv32_artix7_data):
    """Check selected timing report fields"""

    rpt = picorv32_artix7_data["timing"]

    assert rpt["Design Timing Summary"]["TNS(ns)"][0] == -4.140
    assert rpt["Clock Summary"]["Frequency(MHz)"][0] == 200

    # Make sure there are 0 rows
    assert rpt["Other Path Groups Table"].shape[0] == 0

    cols = rpt["Other Path Groups Table"].columns
    assert [cols[i] for i in [0, -1]] == ["Path Group", "THS Total Endpoints"]


@pytest.fixture(scope="module")
def picorv32_kusp_data():
    from edalize.vivado_reporting import VivadoReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/vivado-kintex_usp/impl")

    rpt = VivadoReporting.report(str(data_dir))

    return rpt


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_picorv32_kusp_summary(picorv32_kusp_data):
    """Check all summary fields"""

    summary = picorv32_kusp_data["summary"]

    check_types(summary)

    expected = {
        "lut": 999,
        "reg": 920,
        "blkmem": 0,
        "dsp": 0,
        "constraint": {"clk": 200},
        "fmax": {"clk": 207.6412},
    }

    assert round_fmax(summary, 4) == expected


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_picorv32_kusp_resources(picorv32_kusp_data):
    """Check selected resource report fields"""

    tables = picorv32_kusp_data["resources"]

    df = tables["CLB Logic Distribution"].set_index("Site Type")

    assert df.loc["Register driven from outside the CLB", "Used"] == 260
    assert pd.isna(df.loc["Register driven from outside the CLB", "Available"])

    df = tables["Primitives"].set_index("Ref Name")

    assert df.loc["RAMD32", "Used"] == 84

    # Make sure there are 0 rows
    assert tables["Instantiated Netlists"].shape[0] == 0
    assert list(tables["Instantiated Netlists"].columns) == ["Ref Name", "Used"]


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_picorv32_kusp_timing(picorv32_kusp_data):
    """Check selected timing report fields"""

    rpt = picorv32_kusp_data["timing"]

    assert rpt["Design Timing Summary"]["WNS(ns)"][0] == 0.184
    assert rpt["Clock Summary"]["Period(ns)"][0] == 5.0

    # Make sure there are 0 rows
    assert rpt["Inter Clock Table"].shape[0] == 0

    cols = rpt["Inter Clock Table"].columns
    assert [cols[i] for i in [0, -2]] == ["From Clock", "THS Failing Endpoints"]


@pytest.fixture(scope="module")
def linux_on_litex_vexriscv_arty_a7_data():
    from edalize.vivado_reporting import VivadoReporting

    data_dir = Path(tests_dir + "/test_reporting/data/linux-on-litex-vexriscv/arty_a7")

    # The LiteX script doesn't use the default report names produced by launch_runs

    resources = VivadoReporting.report_resources(
        str(data_dir / "top_utilization_place.rpt")
    )

    timing = VivadoReporting.report_timing(str(data_dir / "top_timing.rpt"))
    summary = VivadoReporting.report_summary(resources, timing)

    result = {"summary": summary, "resources": resources, "timing": timing}
    return result


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_linux_on_litex_vexriscv_arty_a7_summary(linux_on_litex_vexriscv_arty_a7_data):
    summary = linux_on_litex_vexriscv_arty_a7_data["summary"]

    check_types(summary, allowed=[int, float, type(None)])

    expected = {
        "lut": 8297,
        "reg": 5434,
        "blkmem": 29.5,
        "dsp": 4,
        "constraint": {
            "clk100": 100,
            "builder_pll_fb": 100,
            "main_crg_clkout0": 100,
            "builder_mmcm_fb": 100,
            "main_crg_clkout1": 200,
            "main_crg_clkout2": 400,
            "main_crg_clkout3": 400,
            "main_crg_clkout4": 200,
            "main_crg_clkout5": 25,
            "eth_rx_clk": 25,
            "eth_tx_clk": 25,
        },
        "fmax": {
            "clk100": None,
            "builder_pll_fb": None,
            "main_crg_clkout0": 102.5431,
            "builder_mmcm_fb": None,
            "main_crg_clkout1": 340.8316,
            "main_crg_clkout2": None,
            "main_crg_clkout3": None,
            "main_crg_clkout4": 516.5289,
            "main_crg_clkout5": None,
            "eth_rx_clk": 107.8051,
            "eth_tx_clk": 76.8462,
        },
    }

    assert round_fmax(summary, 4) == expected


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_linux_on_litex_vexriscv_arty_a7_resources(
    linux_on_litex_vexriscv_arty_a7_data,
):
    rpt = linux_on_litex_vexriscv_arty_a7_data["resources"]

    df = rpt["Slice Logic Distribution"].set_index("Site Type")
    assert df.loc["Slice", "Util%"] == 33.69
    assert df.loc["LUT as Distributed RAM", "Used"] == 1932


@pytest.mark.skipif(
    PANDAS_VERSION >= (2, 1, 0), reason="apply(...,error='ignore') ignored"
)
def test_linux_on_litex_vexriscv_arty_a7_timing(linux_on_litex_vexriscv_arty_a7_data):
    rpt = linux_on_litex_vexriscv_arty_a7_data["timing"]

    assert rpt["Design Timing Summary"]["TNS(ns)"][0] == 0.0
    assert rpt["Design Timing Summary"]["WNS(ns)"][0] == 0.248

    assert rpt["Clock Summary"].shape == (11, 4)
    df = rpt["Clock Summary"].set_index("Clock")

    assert df["Period(ns)"][-1] == 40.0

    assert df.loc["main_crg_clkout3", "Waveform(ns)"] == "{0.625 1.875}"


@pytest.fixture(scope="module")
def linux_on_litex_vexriscv_de10nano_data():
    from edalize.quartus_reporting import QuartusReporting

    data_dir = Path(tests_dir + "/test_reporting/data/linux-on-litex-vexriscv/de10nano")

    rpt = QuartusReporting.report(str(data_dir))

    return rpt


def test_linux_on_litex_vexriscv_de10nano_summary(
    linux_on_litex_vexriscv_de10nano_data,
):
    summary = linux_on_litex_vexriscv_de10nano_data["summary"]

    check_types(summary)

    expected = {
        "lut": 4317,
        "reg": 3821,
        "blkmem": 87,
        "dsp": 4,
        "constraint": {"clk50": 50},
        "fmax": {"clk50": 69.65},
    }

    assert summary == expected


def test_linux_on_litex_vexriscv_de10nano_resources(
    linux_on_litex_vexriscv_de10nano_data,
):
    rpt = linux_on_litex_vexriscv_de10nano_data["resources"]

    df = rpt["Fitter DSP Block Usage Summary"].set_index("Statistic")
    assert df.loc["Total number of DSP blocks", "Number Used"] == 4

    df = rpt["Fitter Resource Utilization by Entity"].set_index(
        "Compilation Hierarchy Node"
    )
    assert (
        df.loc["|VexRiscv:VexRiscv|", "[A] ALMs used in final placement"]
        == "1810.0 (1574.2)"
    )


def test_linux_on_litex_vexriscv_de10nano_timing(linux_on_litex_vexriscv_de10nano_data):
    rpt = linux_on_litex_vexriscv_de10nano_data["timing"]

    df = rpt["Clocks"].set_index("Clock Name")
    assert df.loc["clk50", "Period"] == 20

    assert (
        rpt["Slow 1100mV 100C Model Fmax Summary"]["Restricted Fmax"][0] == "69.65 MHz"
    )

    df = rpt["Multicorner Timing Analysis Summary"].set_index("Clock")

    assert df.loc["Worst-case Slack", "Setup"] == 5.642
    assert df.loc["Design-wide TNS", "Hold"] == 0


@pytest.fixture(scope="module")
def linux_on_litex_vexriscv_pipistrello_data():
    from edalize.ise_reporting import IseReporting

    data_dir = Path(
        tests_dir + "/test_reporting/data/linux-on-litex-vexriscv/pipistrello"
    )

    rpt = IseReporting.report(str(data_dir))

    return rpt


def test_linux_on_litex_vexriscv_pipistrello_summary(
    linux_on_litex_vexriscv_pipistrello_data,
):
    rpt = linux_on_litex_vexriscv_pipistrello_data["summary"]

    check_types(rpt, allowed=[int, float, str, type(None)])

    expected = {
        "lut": 4760,
        "reg": 3913,
        "blkmem": 53,
        "dsp": 4,
        "constraint": {
            "PRDsys_clk": "12 ns",
            "PRDclk50": "20 ns",
            "soclinux_crg_clk50b": "TSclk50",
            "soclinux_crg_pll_sdram_half_b": "TS_soclinux_crg_clk50b / 3.33333333 PHASE 4.16666667 ns",
            "soclinux_crg_pll_sys": "TS_soclinux_crg_clk50b / 1.66666667",
            "soclinux_crg_pll_sdram_full": "TS_soclinux_crg_clk50b / 6.66666667",
            "soclinux_crg_pll_sdram_half_a": "TS_soclinux_crg_clk50b / 3.33333333 PHASE 4.5 ns",
        },
        "fmax": {
            "PRDsys_clk": 320.1024,
            "PRDclk50": 1081.0811,
            "soclinux_crg_clk50b": 200,
            "soclinux_crg_pll_sdram_half_b": 578.0347,
            "soclinux_crg_pll_sys": 88.1601,
            "soclinux_crg_pll_sdram_full": None,
            "soclinux_crg_pll_sdram_half_a": 172.4138,
        },
    }

    assert round_fmax(rpt, 4) == expected


def test_linux_on_litex_vexriscv_pipistrello_resources(
    linux_on_litex_vexriscv_pipistrello_data,
):
    rpt = linux_on_litex_vexriscv_pipistrello_data["resources"]

    # Check IOB Properties table
    df = rpt["IOB Properties"].set_index("IOB Name")

    ddr_io = df.filter(regex="ddram_*", axis=0)
    assert (ddr_io["IO Standard"] == "MOBILE_DDR").all()

    # Check Control Set Information table
    df = rpt["Control Set Information"]

    sdram_half_clk = df[df["Clock Signal"] == "sdram_half_clk"]
    sdram_half_clk["Slice Load Count"] == [19, 1]

    sys_clk = df[df["Clock Signal"] == "sys_clk"]
    sys_clk["Bel Load Count"].iat[0] == 436

    # Check Utilization by Hierarchy table
    df = rpt["Utilization by Hierarchy"].set_index("Module")

    assert df.loc["top/", "Slices*"] == "952/2073"
    assert df.loc["++IBusCachedPlugin_cache", "BRAM/FIFO"] == "3/3"


def test_linux_on_litex_vexriscv_pipistrello_timing(
    linux_on_litex_vexriscv_pipistrello_data,
):
    rpt = linux_on_litex_vexriscv_pipistrello_data["timing"]

    assert rpt["min period"] == 11.343
    assert rpt["max clock"] == 88.16

    assert list(sorted(rpt["constraint"].keys())) == [
        "PRDclk50",
        "PRDsys_clk",
        "soclinux_crg_clk50b",
        "soclinux_crg_pll_sdram_full",
        "soclinux_crg_pll_sdram_half_a",
        "soclinux_crg_pll_sdram_half_b",
        "soclinux_crg_pll_sys",
    ]

    assert rpt["constraint"]["soclinux_crg_pll_sys"] == {
        "timespec": "TS_soclinux_crg_pll_sys",
        "constraint": "TS_soclinux_crg_clk50b / 1.66666667",
        "paths": 824701,
        "endpoints": 19823,
        "failing": 0,
        "timing errors": 0,
        "setup errors": 0,
        "hold errors": 0,
        "switching limit errors": 0,
        "min period": 11.343,
    }

    constraint = rpt["constraint"]["soclinux_crg_pll_sdram_half_a"]

    assert (
        constraint["constraint"] == "TS_soclinux_crg_clk50b / 3.33333333 PHASE 4.5 ns"
    )
    assert constraint["endpoints"] == 235
    assert constraint["min period"] == 5.8
