import logging
import re
from typing import Dict, Union

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


class QuartusReporting(Reporting):
    """
    Quartus-specific reporting routines.
    """

    # Override non-default class variables
    _resource_rpt_pattern = "*.fit.rpt"
    _timing_rpt_pattern = "*.sta.rpt"
    _report_encoding = "ISO-8859-1"

    @staticmethod
    def _parse_tables(report_str: str) -> Dict[str, str]:
        """
        Parse the tables from a fitter report.

        Keys are the title of the table, values are the table body
        """

        hline = pp.lineStart() + pp.Word("+", "+-") + pp.lineEnd()

        title = (
            pp.lineStart()
            + ";"
            + pp.SkipTo(";")("title").setParseAction(pp.tokenMap(str.strip))
            + ";"
            + pp.lineEnd()
        )

        # Grab everything until the next horizontal line(s). Tables with
        # column headings will have a horizontal line after the headings and
        # at the end of the table. Odd tables without section headings will
        # only have a single horizontal line.
        data = pp.SkipTo(hline, failOn=pp.lineEnd() * 2, include=True)

        table = hline + title + pp.Combine(hline + data * (1, 2))("body")

        # Make line endings significant
        table.setWhitespaceChars(" \t")

        result = {t.title: t.body for t in table.searchString(report_str)}

        return result

    @classmethod
    def report_timing(cls, report_file: str) -> Dict[str, pd.DataFrame]:
        return cls._report_to_df(cls._parse_tables, report_file)

    @classmethod
    def report_resources(cls, report_file: str) -> Dict[str, pd.DataFrame]:
        return cls._report_to_df(cls._parse_tables, report_file)

    @staticmethod
    def report_summary(
        resources: pd.DataFrame, timing: Dict[str, pd.DataFrame]
    ) -> Dict[str, Union[int, float]]:

        util = resources["Fitter Resource Utilization by Entity"].iloc[0]

        resource_buckets = {
            "lut": ["Logic Cells", "Combinational ALUTs"],
            "reg": ["Dedicated Logic Registers"],
            "blkmem": ["M9Ks", "M10Ks", "M20Ks"],
            "dsp": ["DSP Elements", "DSP Blocks"],
        }

        summary = {}  # type: Dict[str, Union[int, float]]

        # Resources in this table are mostly of the form 345.5 (123.3) and we
        # want the first (total) number
        for k, v in resource_buckets.items():
            key = util.index.intersection(v)[0]
            cell = util.at[key]
            summary[k] = int(str(cell).split()[0])

        # Get a frequency like 175.0 MHz and just return the numeric part
        freq = timing["Clocks"].set_index("Clock Name")["Frequency"]
        summary["constraint"] = freq.str.split(expand=True)[0].astype(float).to_dict()

        # Find the Fmax summary table for the slowest corner, such as "Slow
        # 1200mV 85C Model Fmax Summary". The voltage and temperature will
        # depend on the device, so find the match with the highest
        # temperature.

        slow_fmax = re.compile(
            r"Slow (?P<voltage>\d+)mV (?P<temp>\d+)C Model Fmax Summary"
        )
        title_matches = [slow_fmax.match(title) for title in timing.keys()]

        slow_title = max(
            [t for t in title_matches if t], key=lambda x: x.group("temp")
        ).string

        fmax = timing[slow_title].set_index("Clock Name")["Restricted Fmax"]
        series = fmax.str.split(expand=True)[0].astype(float)
        summary["fmax"] = series.to_dict()

        return summary
