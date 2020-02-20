from pathlib import Path

import pytest
import pandas as pd

from edalize_common import tests_dir


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


def test_picorv32_quartus_cylone4():

    from edalize.quartus_reporting import QuartusReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/quartus-cyclone4")

    rpt = QuartusReporting.report(str(data_dir))

    # Check all summary entries

    assert rpt["summary"]["lut"] == 1632
    assert rpt["summary"]["reg"] == 649
    assert rpt["summary"]["blkmem"] == 2
    assert rpt["summary"]["constraint"] == 175.0
    assert rpt["summary"]["fmax"] == 159.95

    # Check selected resources values

    df = rpt["resources"]["Fitter Resource Usage Summary"].set_index("Resource")

    assert (
        df.loc["Total LABs:  partially or completely used", "Usage"]
        == "283 / 1,395 ( 20 % )"
    )

    df = rpt["resources"]["Fitter Resource Utilization by Entity"].set_index(
        "Compilation Hierarchy Node"
    )

    assert df.loc["|altsyncram:cpuregs_rtl_0|", "Memory Bits"] == 1024
    assert df.loc["|picorv32", "M9Ks"] == 2
    assert df.loc["|picorv32", "Logic Cells"] == "1632 (1632)"
    assert df.loc["|picorv32", "Dedicated Logic Registers"] == "649 (649)"

    assert (
        list(rpt["resources"].keys())[-1]
        == "Estimated Delay Added for Hold Timing Details"
    )

    # Check selected timing values

    df = rpt["timing"]["Clocks"].set_index("Clock Name")
    assert round(df.loc["clk", "Period"], 3) == 5.714

    df = rpt["timing"]["Slow 1200mV 85C Model Fmax Summary"].set_index("Clock Name")
    assert df.loc["clk", "Fmax"] == "159.95 MHz"


@pytest.fixture
def picorv32_cyclone10_data():
    from edalize.quartus_reporting import QuartusReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/quartus-cyclone10")

    rpt = QuartusReporting.report(str(data_dir))

    return rpt


def test_picorv32_quartus_cyclone10_summary(picorv32_cyclone10_data):
    """ Check all summary fields """

    summary = picorv32_cyclone10_data["summary"]

    assert summary["lut"] == 1137
    assert summary["reg"] == 761
    assert summary["blkmem"] == 2
    assert summary["constraint"] == 175.0
    assert summary["fmax"] == 131.58


def test_picorv32_quartus_cyclone10_no_header(picorv32_cyclone10_data):
    """ Check a table with no header """

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


@pytest.fixture
def picorv32_s6_data():
    from edalize.ise_reporting import IseReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/ise-spartan6")

    rpt = IseReporting.report(str(data_dir))

    return rpt


def test_picorv32_ise_spartan6_summary(picorv32_s6_data):
    """ Check all summary fields """

    summary = picorv32_s6_data["summary"]

    assert summary["lut"] == 1329
    assert summary["reg"] == 959
    assert summary["blkmem"] == 2
    assert summary["constraint"] == 150
    assert round(summary["fmax"], 4) == 91.9371


def test_picorv32_ise_spartan6_multiline(picorv32_s6_data):
    """ Check multi-line headings """
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


def test_picorv32_ise_spartan6_util_by_hier(picorv32_s6_data):
    """ Check "Utilization by Hierarchy" values """

    df = picorv32_s6_data["resources"]["Utilization by Hierarchy"].set_index("Module")

    assert df.loc["+dut", "BRAM/FIFO"] == "2/2"
    assert df.loc["+dut", "LUTs"] == "1158/1158"
    assert df.loc["top/", "Slice Reg"] == "378/959"
    assert df.loc["top/", "Slices*"] == "73/441"
    assert df.loc["+dut", "Slices*"] == "368/368"


def test_picorv32_ise_spartan6_timing(picorv32_s6_data):
    """ Check timing values """

    rpt = picorv32_s6_data["timing"]

    assert rpt["min period"] == 10.877
    assert round(rpt["max clock"], 4) == 91.9371


@pytest.fixture
def picorv32_artix7_data():
    from edalize.vivado_reporting import VivadoReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/vivado-artix7/impl")

    rpt = VivadoReporting.report(str(data_dir))

    return rpt


def test_picorv32_artix7_summary(picorv32_artix7_data):
    """ Check all summary fields """

    summary = picorv32_artix7_data["summary"]

    assert summary["lut"] == 1009
    assert summary["reg"] == 920
    assert summary["blkmem"] == 0
    assert summary["constraint"] == 200
    assert round(summary["fmax"], 4) == 118.1614


def test_picorv32_artix7_resources(picorv32_artix7_data):
    """ Check selected resource report fields """

    rpt = picorv32_artix7_data["resources"]

    df = rpt["Slice Logic"].set_index("Site Type")
    assert df.at["Slice Registers", "Used"] == 920

    df = rpt["Memory"].set_index("Site Type")
    assert df.at["RAMB18", "Used"] == 0

    df = rpt["DSP"].set_index("Site Type")
    assert df.at["DSPs", "Used"] == 0
    assert df.at["DSPs", "Available"] == 740


def test_picorv32_artix7_timing(picorv32_artix7_data):
    """ Check selected timing report fields """

    rpt = picorv32_artix7_data["timing"]

    assert rpt["Design Timing Summary"]["TNS(ns)"][0] == -4.140
    assert rpt["Clock Summary"]["Frequency(MHz)"][0] == 200

    # Make sure there are 0 rows
    assert rpt["Other Path Groups Table"].shape[0] == 0

    cols = rpt["Other Path Groups Table"].columns
    assert [cols[i] for i in [0, -1]] == ["Path Group", "THS Total Endpoints"]


@pytest.fixture
def picorv32_kusp_data():
    from edalize.vivado_reporting import VivadoReporting

    data_dir = Path(tests_dir + "/test_reporting/data/picorv32/vivado-kintex_usp/impl")

    rpt = VivadoReporting.report(str(data_dir))

    return rpt


def test_picorv32_kusp_summary(picorv32_kusp_data):
    """ Check all summary fields """

    summary = picorv32_kusp_data["summary"]

    assert summary["lut"] == 999
    assert summary["reg"] == 920
    assert summary["blkmem"] == 0
    assert summary["constraint"] == 200
    assert round(summary["fmax"], 4) == 207.6412


def test_picorv32_kusp_resources(picorv32_kusp_data):
    """ Check selected resource report fields """

    tables = picorv32_kusp_data["resources"]

    df = tables["CLB Logic Distribution"].set_index("Site Type")

    assert df.loc["Register driven from outside the CLB", "Used"] == 260
    assert pd.isna(df.loc["Register driven from outside the CLB", "Available"])

    df = tables["Primitives"].set_index("Ref Name")

    assert df.loc["RAMD32", "Used"] == 84

    # Make sure there are 0 rows
    assert tables["Instantiated Netlists"].shape[0] == 0
    assert list(tables["Instantiated Netlists"].columns) == ["Ref Name", "Used"]


def test_picorv32_kusp_timing(picorv32_kusp_data):
    """ Check selected timing report fields """

    rpt = picorv32_kusp_data["timing"]

    assert rpt["Design Timing Summary"]["WNS(ns)"][0] == 0.184
    assert rpt["Clock Summary"]["Period(ns)"][0] == 5.0

    # Make sure there are 0 rows
    assert rpt["Inter Clock Table"].shape[0] == 0

    cols = rpt["Inter Clock Table"].columns
    assert [cols[i] for i in [0, -2]] == ["From Clock", "THS Failing Endpoints"]
