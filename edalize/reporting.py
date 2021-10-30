"""Provide reporting from Edalize backends

Provides common timing and resource information along with as much in-depth
report data as possible. While the detailed data is device-specific it is
reported in a common format, generally a Pandas DataFrame to ease data
analysis.

This module includes the base Reporting class with children for supported
tools in separate modules.

The tests in :mod:`tests/test_reporting.py` are the current best reference
for use of the reporting modules.
"""

import abc
import io
import logging
import pathlib
from typing import Dict, Union, Callable, Optional


logger = logging.getLogger(__name__)

# Reporting is an optional Edalize feature and its required packages may not
# be installed unless Edalize was installed as edalize[reporting]. There is
# currently reduced-functionality feedback, so if the module is used without
# being properly installed log a hopefully helpful error before throwing the
# exception.
import_msg = "Missing package %s. Was edalize installed with the reporting option? (pip install 'edalize[reporting]')"

try:
    import pandas as pd
except ImportError as e:
    logger.exception(import_msg, "pandas")
    raise e


class Reporting(abc.ABC):
    """
    Base class providing defaults and common functionality for tool-specific reporting classes.
    """

    # Static variables to be overridden by subclasses.

    # Glob patterns to find resource and timing reports in a directory
    _resource_rpt_pattern = "*_resource_report.txt"  # type: str
    _timing_rpt_pattern = "*_timing_report.txt"  # type: str

    # The text encoding needed to properly open reports
    _report_encoding = None  # type: Optional[str]

    # The separator used in report tables
    _table_sep = ";"  # type: str

    @staticmethod
    def period_to_freq(
        p: float, in_unit: str = "ns", out_unit: str = "MHz"
    ) -> Optional[float]:
        """
        Convert a clock period to a freqency.
        """

        period_map = {
            "s": 1,
            "ms": 1e-3,
            "us": 1e-6,
            "ns": 1e-9,
            "ps": 1e-12,
        }

        freq_map = {
            "hz": 1,
            "khz": 1e3,
            "mhz": 1e6,
            "ghz": 1e9,
        }

        # Convert for case-insensitive matching
        freq_exp = freq_map.get(out_unit.casefold())
        period_exp = period_map.get(in_unit.casefold())

        if period_exp is None:
            raise ValueError("Unsupported period unit {}".format(in_unit))

        if freq_exp is None:
            raise ValueError("Unsupported frequency unit {}".format(out_unit))

        # Try to handle a None or NaN period value (perhaps a missing value
        # from a report) and numbers as strings ("123.432")
        if p and not pd.isna(float(p)):
            return 1 / (float(p) * period_exp * freq_exp)
        else:
            return None

    @staticmethod
    def table_to_csv(
        table_str: str,
        sep: str = ";",
        new_sep: str = ",",
        hline: str = "+",
        header_threshold: int = 2,
    ) -> Dict[str, Union[bool, str]]:
        """
        Convert report tables to CSV.

        :param table_str: The table to be converted
        :type table_str: str
        :param sep: The cell separator used in the original table (default ";")
        :param new_sep: The cell separator to use in the CSV table (default ",")
        :param hline: Character(s) marking the start of a horizontal line (default "+")
        :param header_threshold: Heuristic to differentiate between tables with only a header and only data

        :return: A dict with the keys

            "header"
                :vartype bool: indicating whether the parsed table had a header
            "csv"
                :vartype str: containing the CSV version of the table
        :rtype: dict(str, bool or str)

        **Example**

        In the following table from a Quartus fit report::

            +---------------------------------------------------------------------------------+
            ; Global & Other Fast Signals Summary                                             ;
            +------+----------+---------+-------------+----------------+----------------------+
            ; Name ; Location ; Fan-Out ; Signal Type ; Promotion Type ; Global Resource Used ;
            +------+----------+---------+-------------+----------------+----------------------+
            ; clk  ; PIN_AA7  ; 713     ; Global      ; Automatic      ; Global Clock Region  ;
            +------+----------+---------+-------------+----------------+----------------------+

        the Quartus parsing routines will remove the title section, resulting
        in this method getting::

            +------+----------+---------+-------------+----------------+----------------------+
            ; Name ; Location ; Fan-Out ; Signal Type ; Promotion Type ; Global Resource Used ;
            +------+----------+---------+-------------+----------------+----------------------+
            ; clk  ; PIN_AA7  ; 713     ; Global      ; Automatic      ; Global Clock Region  ;
            +------+----------+---------+-------------+----------------+----------------------+

        The decorative horizontal lines are removed. The ";" delimiters at the beginning and end of
        each remaining row are also removed along with other whitespace. The
        delimiters and whitespace between cells are replaced with the new
        delimiter resulting in::

            Name,Location,Fan-Out,Signal Type,Promotion Type,Global Resource Used
            clk,PIN_AA7,713,Global,Automatic,Global Clock Region

        **Header detection**

        This routine attempts to detect the uncommon case of a table with no
        header row like the following: ::

            +------------------------------------+---------------------------------------------+
            ; Fitter Status                      ; Successful - Wed Dec  4 13:37:55 2019       ;
            ; Quartus Prime Version              ; 18.1.0 Build 625 09/12/2018 SJ Lite Edition ;
            ; Revision Name                      ; picorv32_wrap_0_1                           ;
            ; Top-level Entity Name              ; picorv32                                    ;
            ; Family                             ; Cyclone IV E                                ;
            ; Device                             ; EP4CE22F17C6                                ;
            ; Timing Models                      ; Final                                       ;
            ; Total logic elements               ; 1,632 / 22,320 ( 7 % )                      ;
            ;     Total combinational functions  ; 1,584 / 22,320 ( 7 % )                      ;
            ;     Dedicated logic registers      ; 649 / 22,320 ( 3 % )                        ;
            ; Total registers                    ; 649                                         ;
            ; Total pins                         ; 1 / 154 ( < 1 % )                           ;
            ; Total virtual pins                 ; 408                                         ;
            ; Total memory bits                  ; 2,048 / 608,256 ( < 1 % )                   ;
            ; Embedded Multiplier 9-bit elements ; 0 / 132 ( 0 % )                             ;
            ; Total PLLs                         ; 0 / 4 ( 0 % )                               ;
            +------------------------------------+---------------------------------------------+

        However, there may also be similar tables with just a header and no
        data rows like the following: ::

            +----------+------+
            | Ref Name | Used |
            +----------+------+

        This method guesses that a table with only leading and trailing
        horizontal lines with less than or equal to ``header_threshold`` rows
        has a header (and no data rows)

        **Multirow Headers**

        Table-reading routines like Pandas ``read_csv`` don't like the header
        being spread over multiple rows as in ::

            +-------------------------------------...-+
            | IOB Name | Type | Diff | Drive    | ... |
            |          |      | Term | Strength | ... |
            +-----------------------------------------+
            ...

        This method joins the header columns to a single row

        **Alternatives**

        A library routine may be more robust. For example, the Astropy package
        includes many routines for ASCII table I/O (astropy.io.ascii). The
        FixedWidth routines seem to handle most EDA tool tables, but not the
        multi-row header case.

        The native Pandas table reading routines also don't handle the
        multi-row header case, and they interpret the leading and trailing
        separators as extra columns filled with NaN. This can be handled with
        drop_na, but that's not ideal.
        """

        all_lines = table_str.strip().splitlines()
        lines = [l for l in all_lines if not l.startswith(hline)]

        # Get the positions of any horizontal lines
        hline_index = [i for i, l in enumerate(all_lines) if l.startswith(hline)]

        # Decide whether there is a header row
        #
        # Assume there is no header if the only horizontal lines are the first
        # and last line and there are more data rows than the threshold.

        has_header = True

        if hline_index == [0, len(all_lines) - 1] and len(lines) > header_threshold:
            has_header = False

        csv_lines = []

        for l in lines:
            # Remove leading and trailing whitespace and separators. Do this
            # in two steps or it will consume empty cells like
            #
            # |    |    |    | alpha | beta |   |   |

            clean_line = l.strip().strip(sep)

            # Split the line by the separator, clean any whitespace, and
            # rejoin the line with the new separator. The cell will be quoted
            # if it contains the new separator.

            new_line = []
            for cell in clean_line.split(sep):
                clean_cell = cell.strip()
                # Quote the cell if it contains the new separator
                if new_sep in clean_cell:
                    clean_cell = '"{}"'.format(clean_cell)
                new_line.append(clean_cell)

            csv_lines.append(new_sep.join(new_line))

        # Identify header rows and merge them into a single row since Pandas
        # read_csv and other table tools don't seem to handle merging them.

        header_row_count = hline_index[1] - hline_index[0] - 1

        if has_header and header_row_count > 1:
            head = [l.split(new_sep) for l in csv_lines[:header_row_count]]

            new_head = []

            for c in range(len(head[0])):
                new_col = []
                for r in range(len(head)):
                    new_col.append(head[r][c].strip())
                new_head.append(" ".join(new_col).strip())

            # Remove the old header lines and insert the new one
            del csv_lines[:header_row_count]
            csv_lines.insert(0, new_sep.join(new_head))

        table = "\n".join(csv_lines)

        return {"header": has_header, "csv": table}

    @classmethod
    def _report_to_df(
        cls, parser: Callable[[str], Dict], report_file: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Helper for reports returning a number of tables.

        :param parser: The function to be used to parse the report
            string. Should return a dictionary with keys containing the table
            name and values containing the table
        :type parser: func
        :param report_file: Report file name
        :type report_file: str

        :return: A dictionary with the table names as keys and values containing a
            Pandas DataFrame with the data from the ASCII table.
        :rtype: dict
        """

        report = open(report_file, "r", encoding=cls._report_encoding).read()

        tables = {}
        for k, v in parser(report).items():
            table = cls.table_to_csv(v, sep=cls._table_sep)

            header = "infer" if table["header"] else None

            # Mypy wants some assurance we're passing a string and not a bool
            # to StringIO. We need the new TypedDict here or just to use a
            # string instead of a bool for the header
            assert isinstance(table["csv"], str)

            df = pd.read_csv(io.StringIO(table["csv"]), header=header)

            tables[k] = df

        return tables

    @classmethod
    @abc.abstractmethod
    def report_summary(cls, resources, timing):
        """
        Resource summary in a backend-independent format.

        This abstract method should be overridden by each backend.

        :param resources: Detailed resource information for summarising.
        :param timing: Detailed timing information for summarising

        :return: A dictionary with the keys

            * "constraint": Clock constraint in MHz
            * "fmax": Maximum clock in MHz
            * "lut": Number of look-up tables used
            * "reg": Number of registers used
            * "blkmem": Number of embedded memory blocks used
            * "dsp": Number of DSP blocks used
        :rtype: dict

        Summarises a subset of the available timing and resource information,
        meant to provide a backend-independent way to get some information.
        For timing a single clock is assumed. Given the differences in FPGA
        resources between devices a standard set is more difficult, but each
        backend implementation will do its best to map actual device resources
        to the above resource categories.
        """

        pass

    @classmethod
    def report_resources(cls, report_file: str):
        """
        Detailed device-dependent resource information.

        This abstract method should be overridden by each backend.

        :param report_file: The file name for the resource report to be parsed
        :type report_file: str

        :return: Detailed backend and device-specific resource information. The
            current classes report this as a dictionary where the keys are the
            title of the table from the resource report and the values are Pandas
            DataFrames.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def report_timing(cls, report_file: str):
        """
        Detailed device-dependent timing information.

        This abstract method should be overridden by each backend.

        Args:

            report_file: The file name for the resource report to be parsed

        Returns:

            Detailed backend and device-specific timing information.
        """
        pass

    @classmethod
    def report(cls, dir: str) -> Dict[str, pd.DataFrame]:
        """
        Report a common summary format along with device-specific resource and timing information.

        The :func:`report_summary`, :func:`report_resources`, and
        :func:`report_timing` methods may be used to access the data for each
        key individually.

        :param dir: The directory containing the resource and timing reports
        :type dir: str

        :return: A dictionary with the following keys:

            "summary"
                Summarisation from report_summary method

            "resources"
                Detailed backend and device-specific resource information.
                The current classes report this as a dictionary where the
                keys are the title of the table from the resource report
                and the values are Pandas DataFrames.

            "timing"
                Detailed backend and device-specific timing information.
        :rtype: dict(str, pandas.DataFrame)
        """

        result = {"summary": None, "resources": None, "timing": None}

        report_dir = pathlib.Path(dir)
        resource_rpt = list(report_dir.glob(cls._resource_rpt_pattern))
        timing_rpt = list(report_dir.glob(cls._timing_rpt_pattern))

        # For now we'll be inflexible an expect one match for each type of
        # report
        if len(resource_rpt) != 1 or len(timing_rpt) != 1:
            logger.error(
                "Found {} utilization and {} timing reports in directory {}".format(
                    len(resource_rpt), len(timing_rpt), dir
                )
            )
            return result

        resources = cls.report_resources(str(resource_rpt[0]))
        timing = cls.report_timing(str(timing_rpt[0]))
        summary = cls.report_summary(resources, timing)
        result = {"summary": summary, "resources": resources, "timing": timing}
        return result
