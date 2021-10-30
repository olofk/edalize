"""
Vivado-specific reporting routines
"""

import io
import logging
from typing import Dict, Union, Optional

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
except ImportError as e:
    logger.exception(import_msg, "pyparsing")
    raise e

try:
    import pandas as pd
except ImportError as e:
    logger.exception(import_msg, "pandas")
    raise e


class VivadoReporting(Reporting):

    # Override non-default class variables
    _resource_rpt_pattern = "*_utilization_placed.rpt"
    _timing_rpt_pattern = "*_timing_summary_routed.rpt"
    _table_sep = "|"

    @staticmethod
    def _parse_utilization_tables(util_str: str) -> Dict[str, str]:
        """
        Find all of the section titles and tables in a Vivado utilization report.

        These are returned as a dict with the section titles as keys and the table as the value.
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
        """
        Return tables from a Vivado timing summary report.

        This currently only handles basic tables such as "Design Timing
        Summary" and "Clock Summary". The more complex data in "Timing Details"
        such as worst paths, etc. isn't parsed.
        """

        # Make newlines widely significant but be careful not to effect others
        saved_whitespace = pp.ParserElement.DEFAULT_WHITE_CHARS
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
        pp.ParserElement.setDefaultWhitespaceChars(saved_whitespace)

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
        # These tables don't have delimiters other than two or more spaces,
        # but read_fwf seems to find the columns correctly. We'd like to
        # eliminate the dashes that separate headings from data. The comment
        # argument can do this, but that seems to prevent read_fwf from
        # correctly guessing the column widths. Instead we'll just let them
        # show up and then drop this row. It's row 0 in known examples, but
        # this more carefully drops rows where all the column values are
        # dashes.
        #
        # Currently read_fwf doesn't seem to be inferring data types
        # correctly, leaving everything as objects and causing errors during
        # arithmetic. The infer_objects() function doesn't seem to change
        # anything, and convert_dtypes() just results in strings. Currently
        # applying to_numeric to every column gives the best results.

        df_dict = {}

        for k, v in timing.items():
            df = pd.read_fwf(io.StringIO(v))

            # Drop the dashes separating the headers from data
            #
            # Find rows where all columns are dashes and get their indicies as
            # a list
            dash_row = df.apply(lambda s: s.str.match(r"^-+$", na=False)).all(
                axis="columns"
            )
            dash_row_idx = dash_row[dash_row].index

            # Drop the dashed rows and reset the index so that the separator
            # rows don't leave holes in the index making indexing more
            # difficult
            df = df.drop(dash_row_idx).reset_index(drop=True)

            # Convert numeric values that read_fwf doesn't seem to be
            # handling, perhaps due to the dashes.
            df = df.apply(pd.to_numeric, errors="ignore", raw=True)

            df_dict[k] = df

        return df_dict

    @staticmethod
    def report_summary(
        resources: Dict[str, pd.DataFrame], timing: Dict[str, pd.DataFrame]
    ) -> Dict[str, Union[int, float, Dict[str, Optional[float]]]]:

        summary = {}  # type: Dict[str, Union[int, float, Dict[str, Optional[float]]]]

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
        summary["lut"] = df.loc[lut, "Used"].item()
        summary["reg"] = df.loc[reg, "Used"].item()

        if "Memory" in resources:
            table = "Memory"
        elif "BLOCKRAM" in resources:
            table = "BLOCKRAM"
        else:
            logger.error("Can't find a table with memory information")
            return summary

        df = resources[table].set_index("Site Type")
        summary["blkmem"] = df.loc["Block RAM Tile", "Used"].item()

        if "DSP" in resources:
            table = "DSP"
        elif "ARITHMETIC" in resources:
            table = "ARITHMETIC"
        else:
            logger.error("Can't find a table with memory information")
            return summary

        df = resources[table].set_index("Site Type")
        summary["dsp"] = df.loc["DSPs", "Used"].item()

        # Return a dict indexed by the clock name
        df = timing["Clock Summary"].set_index("Clock")

        summary["constraint"] = df["Frequency(MHz)"].to_dict()

        # Loadless clocks won't have a WNS entry which maps to NaN. This will
        # be mapped to None by period_to_df which feels more appropriate.
        # Pandas.Series.transform or apply feel like the most appropriate
        # functions to use, but seem to interpret the returned None as a
        # no-op, so the mapping is done when the returned dictionary is
        # created.
        period = timing["Clock Summary"].set_index("Clock")["Period(ns)"]
        wns = timing["Intra Clock Table"].set_index("Clock")["WNS(ns)"]

        summary["fmax"] = {
            k: Reporting.period_to_freq(v) for k, v in (period - wns).to_dict().items()
        }

        return summary
