"""ISE-specific reporting routines
"""

import logging
from typing import Dict

import pyparsing as pp
from pyparsing import pyparsing_common as ppc
import pandas as pd

from edalize.reporting import Reporting

logger = logging.getLogger(__name__)


class IseReporting(Reporting):

    # Override class variables
    resource_rpt_pattern = "*_map.mrp"
    timing_rpt_pattern = "*.twr"
    table_sep = "|"

    @staticmethod
    def _parse_twr(timing_str: str) -> pp.ParseResults:
        """Parse ISE timing report

        Very far from comprehensive. Only handles a single clock specified in MHz
        """
        # Look for a section of the report like the following and extract the
        # constraint and minimum period.
        #
        # ================================================================================
        # Timing constraint: TS_clk = PERIOD TIMEGRP "clk" 150 MHz HIGH 50%;
        # For more information, see Period Analysis in the Timing Closure User Guide (UG612).
        #
        # 39892 paths analyzed, 3774 endpoints analyzed, 632 failing endpoints
        # 632 timing errors detected. (632 setup errors, 0 hold errors, 0 component switching limit errors)
        # Minimum period is  10.877ns.
        # --------------------------------------------------------------------------------

        # This should support ns or spellings like Mhz but doesn't
        clock = ppc.integer("constraint") + pp.Suppress("MHz")
        period = ppc.real("min period") + pp.Suppress("ns")

        constraint = pp.Suppress("Timing constraint:" + pp.SkipTo(clock)) + clock

        min_period = pp.Suppress("Minimum period is") + period

        top = pp.Suppress(pp.SkipTo(constraint))
        mid = pp.Suppress(pp.SkipTo(min_period))

        report = top + constraint + mid + min_period

        result = report.parseString(timing_str)

        return result

    @staticmethod
    def _parse_map_tables(report_str: str) -> Dict[str, str]:
        """Parse the tables from a ISE map report

        Keys are the title of the table, values are the table body
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

        # Grab everything until the next horizontal lines. The first data is the
        # column headings, the second the values
        data = pp.SkipTo(hline, failOn=pp.lineEnd() * 2, include=True)

        table = title + sec_hline + pp.Combine(hline + data * 2)("body")

        # Make line endings significant
        table.setWhitespaceChars(" \t")

        result = {t.title: t.body for t in table.searchString(report_str)}

        return result

    @classmethod
    def report_resources(cls, report_file: str) -> Dict[str, pd.DataFrame]:
        """Report resource data from a map report

        Parse a provided map report and return the tables from the report
        in a dictionary keyed with the table title and a Pandas DataFrame
        as the value
        """

        return cls._report_to_df(cls._parse_map_tables, report_file)

    @classmethod
    def report_timing(cls, report_file: str) -> pd.Series:
        """Report clock constraint, minimum period, and computed maximum frequency
        """

        report = open(report_file, "r").read()

        data = cls._parse_twr(report)

        timing = data.asDict()
        timing["max clock"] = 1000.0 / timing["min period"]

        return pd.Series(timing)

    @staticmethod
    def report_summary(
        resources: Dict[str, pd.DataFrame], timing: Dict[str, pd.DataFrame]
    ) -> Dict[str, int]:

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

        summary = {}

        # Resources in this table are of the form 123/456 and we want the
        # second (total) number
        for k in resource_buckets.keys():
            cell = util.iloc[0].at[resource_buckets[k]]
            summary[k] = int(str(cell).split("/")[1])

        summary["constraint"] = timing["constraint"]
        summary["fmax"] = timing["max clock"]

        return summary
