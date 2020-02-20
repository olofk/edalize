"""Vivado-specific reporting routines
"""

import io
import logging
from typing import Dict, Union

import pyparsing as pp
import pandas as pd

from edalize.reporting import Reporting

logger = logging.getLogger(__name__)


class VivadoReporting(Reporting):

    # Override non-default class variables
    resource_rpt_pattern = "*_utilization_placed.rpt"
    timing_rpt_pattern = "*_timing_summary_routed.rpt"
    table_sep = "|"

    @staticmethod
    def _parse_utilization_tables(util_str: str) -> Dict[str, str]:
        """Find all of the section titles and tables in a Vivado utilization report

        These are returned as a dict with the section titles as keys and the
        table as the value
        """

        # Find section headings, discarding the number and following horizontal
        # line. For example:
        #
        # 1.1 Summary of Registers by Type
        # --------------------------------

        sec_num = pp.Suppress(pp.lineStart() + pp.Word(pp.nums + "."))
        sec_title = sec_num + pp.SkipTo(pp.lineEnd())("title") + pp.lineEnd().suppress()

        # -------------------------------
        sec_hline = pp.Suppress(pp.lineStart() + pp.Word("-") + pp.lineEnd())
        sec_head = sec_title + sec_hline + pp.lineEnd().suppress()

        # Tables use horizontal lines with like the following to mark column
        # headings and the end of the table:
        #
        # +------+------+-------+

        table_hline = pp.lineStart() + pp.Word("+", "-+") + pp.lineEnd()

        # Tables may just be a header with no data rows, or a full header and
        # data rows, so there will be one or two more horizontal lines.

        data = pp.SkipTo(table_hline, failOn=pp.lineEnd() * 2, include=True)

        table = pp.Combine(table_hline + data * (1, 2))

        section = sec_head + table("table")

        # Make line endings significant
        section.setWhitespaceChars(" \t")

        table_dict = {x["title"]: x["table"] for x in section.searchString(util_str)}

        return table_dict

    @staticmethod
    def _parse_timing_summary_tables(time_rpt: str):
        """Return tables from a Vivado timing summary report

        This currently only handles basic tables such as "Design Timing
        Summary" and "Clock Summary". The more complex data in "Timing Details"
        such as worst paths, etc. isn't parsed.
        """

        pp.ParserElement.setDefaultWhitespaceChars(" \t")

        # Extract table title ("Clock Summary") from a section heading like:
        #
        # --------------------------------------------------------------
        # | Clock Summary
        # | -------------
        # --------------------------------------------------------------
        sec_hline = pp.lineStart() + pp.Word("-") + pp.lineEnd()
        sec_row_start = pp.lineStart() + pp.Literal("|").suppress()
        sec_title = (
            sec_row_start + pp.SkipTo(pp.lineEnd())("title") + pp.lineEnd().suppress()
        )
        sec_title_uline = sec_row_start + pp.Suppress(pp.Word("-") + pp.lineEnd())

        section_head = sec_hline + sec_title + sec_title_uline + sec_hline

        blank_line = pp.Suppress(pp.lineEnd() * 2)

        # Tables are headings followed by lines and then data.
        #
        # Clock  Waveform(ns)         Period(ns)      Frequency(MHz)
        # -----  ------------         ----------      --------------
        # clk    {0.000 2.500}        5.000           200.000

        # Match two or more groups of dashes to avoid matching long single
        # horizontal lines used elsewhere. Normally the spaces between the
        # groups of dashes would be consumed, so get them back with
        # originalTextFor(). It would be safer to anchor this to the start of
        # the line, but "Design Timing Summary" and perhaps others indent the
        # table for some reason

        table_hline = pp.originalTextFor(pp.Word("-") * (2,) + pp.lineEnd())

        # Get any header rows above the horizontal lines
        table_head = pp.SkipTo(table_hline, failOn=blank_line)

        # Get everything from the horizontal lines to an empty line
        table_body = pp.SkipTo(blank_line)

        # The adjacent argument shouldn't be required but it doesn't match
        # anything without it. It seems like the newline at the end of the
        # heading row may not be getting included somehow.

        table = pp.Combine(table_head + table_hline + table_body, adjacent=False)(
            "table"
        )

        section = section_head + pp.lineEnd().suppress() + table

        # Restore whitespace characters
        pp.ParserElement.setDefaultWhitespaceChars(pp.ParserElement.DEFAULT_WHITE_CHARS)

        table_dict = {x["title"]: x["table"] for x in section.searchString(time_rpt)}

        return table_dict

    @classmethod
    def report_resources(cls, report_file: str) -> Dict[str, pd.DataFrame]:

        return cls._report_to_df(cls._parse_utilization_tables, report_file)

    @classmethod
    def report_timing(cls, report_file: str) -> Dict[str, pd.DataFrame]:

        report = open(report_file, "r").read()

        timing = cls._parse_timing_summary_tables(report)

        # Convert the list of tables into a dictionary keyed with the title
        # and the value as a DataFrame.
        #
        # These tables don't have delimiters other than two or more spaces.
        # The comment argument allows ignoring the dashes separating headers
        # from data.
        df_dict = {
            k: pd.read_csv(
                io.StringIO(v), sep=r"\s{2,}", comment="---", engine="python"
            )
            for k, v in timing.items()
        }

        return df_dict

    @staticmethod
    def report_summary(
        resources: Dict[str, pd.DataFrame], timing: Dict[str, pd.DataFrame]
    ) -> Dict[str, Union[int, float]]:

        summary: Dict[str, Union[int, float]] = {}

        # Vivado uses different tables and row values for different families.
        # This at least works with the Artix 7 and Kintex Ultrascale+

        if "Slice Logic" in resources:
            table = "Slice Logic"
            lut = "Slice LUTs"
            reg = "Slice Registers"
        elif "CLB Logic" in resources:
            table = "CLB Logic"
            lut = "CLB LUTs"
            reg = "CLB Registers"
        else:
            logger.error("Can't find a table with LUT information")
            return summary

        df = resources[table].set_index("Site Type")
        summary["lut"] = df.loc[lut, "Used"]
        summary["reg"] = df.loc[reg, "Used"]

        if "Memory" in resources:
            table = "Memory"
        elif "BLOCKRAM" in resources:
            table = "BLOCKRAM"
        else:
            logger.error("Can't find a table with memory information")
            return summary

        df = resources[table].set_index("Site Type")
        summary["blkmem"] = df.loc["Block RAM Tile", "Used"]

        if "DSP" in resources:
            table = "DSP"
        elif "ARITHMETIC" in resources:
            table = "ARITHMETIC"
        else:
            logger.error("Can't find a table with memory information")
            return summary

        df = resources[table].set_index("Site Type")
        summary["dsp"] = df.loc["DSPs", "Used"]

        summary["constraint"] = timing["Clock Summary"].at[0, "Frequency(MHz)"]
        summary["fmax"] = 1000.0 / (
            timing["Clock Summary"].at[0, "Period(ns)"]
            - timing["Design Timing Summary"].at[0, "WNS(ns)"]
        )

        return summary
