import logging
from typing import Dict, Any

from edalize.reporting import Reporting

logger = logging.getLogger(__name__)

# Reporting is an optional Edalize feature and its required packages may not
# be installed unless Edalize was installed as edalize[reporting]. There is
# currently reduced-functionality feedback, so if the module is used without
# being properly installed log a hopefully helpful error before throwing the
# exception.
import_msg = "Missing package %s. Was edalize installed with the reporting option? (pip install 'edalize[reporting]')"

# This would perhaps be cleaner but more complex with importlib

try:
    import pyparsing as pp
    from pyparsing import pyparsing_common as ppc
except ImportError as e:
    logger.exception(import_msg, "pyparsing")
    raise e

try:
    import pandas as pd
except ImportError as e:
    logger.exception(import_msg, "pandas")
    raise e


class IseReporting(Reporting):
    """
    ISE-specific reporting routines.
    """

    # Override class variables
    _resource_rpt_pattern = "*_map.mrp"
    _timing_rpt_pattern = "*.twr"
    _table_sep = "|"

    @staticmethod
    def _parse_twr_period(timing_str: str) -> pp.ParseResults:
        """
        Parse period constraints from an ISE timing report.

        Expects the default ISE verbose output from a command like: ::
            trce -v 3 -n 3 -fastpaths top.ncd top.pcf -o top.twr
        """
        # Look for a section of the report like the following and extract the
        # constraint, path information, and minimum period.
        #
        # ================================================================================
        # Timing constraint: TS_clk = PERIOD TIMEGRP "clk" 150 MHz HIGH 50%;
        # For more information, see Period Analysis in the Timing Closure User Guide (UG612).
        #
        # 39892 paths analyzed, 3774 endpoints analyzed, 632 failing endpoints
        # 632 timing errors detected. (632 setup errors, 0 hold errors, 0 component switching limit errors)
        # Minimum period is  10.877ns.
        # --------------------------------------------------------------------------------
        #
        # or
        #
        # ================================================================================
        # Timing constraint: TS_soclinux_crg_pll_sdram_half_b = PERIOD TIMEGRP
        # "soclinux_crg_pll_sdram_half_b" TS_soclinux_crg_clk50b / 3.33333333
        # PHASE 4.16666667 ns HIGH 50%;
        # For more information, see Period Analysis in the Timing Closure User Guide (UG612).
        #
        #  0 paths analyzed, 0 endpoints analyzed, 0 failing endpoints
        #  0 timing errors detected. (0 component switching limit errors)
        #  Minimum period is   1.730ns.
        # --------------------------------------------------------------------------------

        period = ppc.real("min period") + pp.Suppress("ns")

        # Build up a case-insensitive match for any of the below units
        units = ["ps", "ns", "micro", "ms", "%", "MHz", "GHz", "kHz"]

        pp_units = pp.CaselessLiteral(units[0])
        for u in units[1:]:
            pp_units |= pp.CaselessLiteral(u)

        hl = pp.Literal("HIGH") | pp.Literal("LOW")
        num = ppc.number + pp.Optional(pp_units)
        jitter = pp.Optional("INPUT_JITTER" + num)

        # Remove leading and trailing whitespace and any line breaks
        #
        # SkipTo in the below timespec parser will pickup whitespace including
        # new lines if they are included in the report.
        def remove_ws_and_newlines(s):
            lines = [l.strip() for l in s.splitlines()]
            return " ".join(lines)

        timespec = (
            pp.Suppress("Timing constraint:")
            + pp.Word(pp.printables)("timespec")
            + pp.Suppress("= PERIOD TIMEGRP")
            + pp.Word(pp.printables)("timegroup")
            + pp.SkipTo(hl)("constraint").setParseAction(
                pp.tokenMap(remove_ws_and_newlines)
            )
            + pp.Suppress(hl + num + jitter + ";")
        )

        # Parse the path information from the report like:
        #
        # 0 paths analyzed, 0 endpoints analyzed, 0 failing endpoints
        # 0 timing errors detected. (0 component switching limit errors)
        #
        # or
        #
        # 266 paths analyzed, 235 endpoints analyzed, 0 failing endpoints
        # 0 timing errors detected. (0 setup errors, 0 hold errors, 0 component switching limit errors)
        stats = (
            ppc.integer("paths")
            + pp.Suppress("paths analyzed,")
            + ppc.integer("endpoints")
            + pp.Suppress("endpoints analyzed,")
            + ppc.integer("failing")
            + pp.Suppress("failing endpoints")
            + ppc.integer("timing errors")
            + pp.Suppress("timing errors detected. (")
            + pp.Optional(
                ppc.integer("setup errors")
                + pp.Suppress("setup errors,")
                + ppc.integer("hold errors")
                + pp.Suppress("hold errors,")
            )
            + ppc.integer("switching limit errors")
            + pp.Suppress("component switching limit errors)")
        )

        # It's not clear why this doesn't show up for one timing constraint in
        # the LiteX Linux VexRISCV example
        min_period = pp.Optional(pp.Suppress("Minimum period is") + period)

        constraint = timespec + pp.Suppress(pp.SkipTo(stats)) + stats + min_period

        result = constraint.searchString(timing_str)

        return result

    @staticmethod
    def _parse_twr_stats(report_str: str) -> pp.ParseResults:
        """
        Parse the design statistics from an ISE timing report.

        Design statistics: ::
           Minimum period:  11.343ns{1}   (Maximum frequency:  88.160MHz)
        """

        header = pp.Suppress(pp.SkipTo("Design statistics:", include=True))
        period = (
            pp.Suppress("Minimum period:")
            + ppc.number("min period")
            + pp.Suppress("ns{1}")
        )
        freq = (
            pp.Suppress("(Maximum frequency:")
            + ppc.number("max clock")
            + pp.Suppress("MHz)")
        )

        stat = header + period + freq

        return stat.parseString(report_str)

    @staticmethod
    def _parse_map_tables(report_str: str) -> Dict[str, str]:
        """
        Parse the tables from a ISE map report.

        Keys are the title of the table, values are the table body.
        """

        # Capture the title from section headings like:
        #
        # Section 12 - Control Set Information
        # ------------------------------------

        title = (
            pp.lineStart()
            + "Section"
            + ppc.integer
            + "-"
            + pp.SkipTo(pp.lineEnd())("title").setParseAction(pp.tokenMap(str.strip))
            + pp.lineEnd()
        )

        sec_hline = pp.Suppress(pp.lineStart() + pp.Word("-") + pp.lineEnd() * (1,))

        # Table horizontal lines like
        # +-------------------------------+
        hline = pp.lineStart() + pp.Word("+", "+-") + pp.lineEnd()

        # Most tables will have the format
        # +-----------------------+
        # | Col 1 | Col 2 | Col 3 |
        # +-----------------------+
        # | D1    | D2    | D3    |
        # ...
        # +-----------------------+
        #
        # However "Control Set Information" appears to use horizontal lines to
        # separate clocks within the data section. Therefore, just grab
        # everything until a horizontal line followed by a blank line rather
        # than something more precise.

        table = pp.Combine(hline + pp.SkipTo(hline + pp.LineEnd(), include=True))(
            "body"
        )
        table_section = title + sec_hline + table

        # Make line endings significant
        table_section.setWhitespaceChars(" \t")

        result = {t.title: t.body for t in table_section.searchString(report_str)}

        return result

    @classmethod
    def report_resources(cls, report_file: str) -> Dict[str, pd.DataFrame]:
        """
        Report resource data from a map report.

        Parse a provided map report and return the tables from the report
        in a dictionary keyed with the table title and a Pandas DataFrame
        as the value
        """

        return cls._report_to_df(cls._parse_map_tables, report_file)

    @classmethod
    def report_timing(cls, report_file: str) -> Dict[str, Any]:
        """
        Report period constraints, and overall minimum period and maximum frequency.
        """

        report = open(report_file, "r").read()

        period = cls._parse_twr_period(report)
        stats = cls._parse_twr_stats(report)

        # Return the "min period" and "max clock" values from the statistics
        # along with a "constraint" key that has a dictionary with some
        # information about the constraints that were found. For now the key
        # is the time group name with and quotes removed and the string
        # constraint value

        timing = stats.asDict()

        timing["constraint"] = {}
        for p in period:
            v = p.asDict()
            k = v.pop("timegroup").strip('"')
            timing["constraint"][k] = v

        return timing

    @staticmethod
    def report_summary(resources: Dict[str, pd.DataFrame], timing: Dict[str, Any]):

        util = resources["Utilization by Hierarchy"]

        # Find a column beginning with DSP since we don't know if it's
        # DSP48A1, DSP48E2, etc.
        dsp_col = [c for c in util.columns if c.startswith("DSP")]

        if len(dsp_col) != 1:
            logger.error("Expected 1 column named DSP but found", len(dsp_col))

        resource_buckets = {
            "lut": "LUTs",
            "reg": "Slice Reg",
            "blkmem": "BRAM/FIFO",
            "dsp": dsp_col[0],
        }

        # The basic resource data is ints, but the timing information is more
        # complex
        summary = {}  # type: Dict[str, Any]

        # Resources in this table are of the form 123/456 and we want the
        # second (total) number
        for k in resource_buckets.keys():
            cell = util.iloc[0].at[resource_buckets[k]]
            summary[k] = int(str(cell).split("/")[1])

        summary["constraint"] = {}
        summary["fmax"] = {}

        # Report the constraint and Fmax value for each timegroup
        for k, v in timing["constraint"].items():
            summary["constraint"][k] = v["constraint"]
            summary["fmax"][k] = Reporting.period_to_freq(v.get("min period"))

        return summary
