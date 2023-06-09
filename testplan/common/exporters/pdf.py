"""
  Utilities for generating pdf files via Reportlab.
"""

import itertools

from reportlab.platypus import Table
from reportlab.lib import colors

from testplan.common.utils.comparison import is_regex
from testplan.common.exporters import constants


# If you increase this too much Reportlab starts having
# performance issues and takes exponentially longer to render the PDF
MAX_TABLE_ROWS = 1000


def _partition_data(data, max_rows):
    """
    Partition a table's data, each partition
    containing at most ``max_rows`` rows.

    :param data: the table data
    :type data: ``list`` of ``list``
    :param max_rows: the maximum number of rows in each partition
    :type max_rows: ``int``
    :return: a generator yielding each new partition
    :rtype: ``generator``
    """
    return (
        data[row : row + max_rows] for row in range(0, len(data), max_rows)
    )


def _partition_style(style, num_rows, max_rows):
    """
    Partition a table's style commands.

    :param style: the style commands
    :type style: ``list`` of ``tuple``
    :param num_rows: the number of rows in the table
    :type num_rows: ``int``
    :param max_rows: the maximum number of rows in each partition
    :type max_rows: ``int``
    :return: a generator yielding a list of style commands
            applicable for each new partition
    :rtype: ``generator``
    """
    for offset in range(0, num_rows, max_rows):
        end_row = min(offset + max_rows, num_rows) - 1
        partition = []

        for command in style:
            start = command[1][1]
            end = command[2][1]

            command_start = num_rows + start if start < 0 else start
            command_end = num_rows + end if end < 0 else end
            command_rows = end_row - offset

            if command_end < offset or command_start > end_row:
                # Not applicable at all
                continue

            partition_start = (
                0 if command_start < offset else command_start - offset
            )

            partition_end = (
                command_rows if command_end > end_row else command_end - offset
            )

            # Replace the old row indices with new ones,
            # but keep the rest of the tuple the same
            partition.append(
                (
                    command[0],
                    (command[1][0], partition_start),
                    (command[2][0], partition_end),
                )
                + command[3:]
            )

        yield partition


def create_base_tables(data, style, col_widths, max_rows=MAX_TABLE_ROWS):
    """
    Create tables for the specified data and style
    commands, partitioning where necessary.

    :param data: the table data
    :type data: ``list`` of ``list``
    :param style: the style commands
    :type style: ``list`` of ``tuple``
    :param col_widths: column widths for the new tables
    :type col_widths: ``iterable``
    :param max_rows: the maximum number of rows in each table
    :type max_rows: ``int``
    :return: a list of new tables
    :rtype: ``list`` of ``Table``
    """
    zipped = zip(
        _partition_data(data, max_rows=max_rows),
        _partition_style(style, len(data), max_rows=max_rows),
    )

    return [
        Table(data=_data, colWidths=col_widths, style=_style)
        for _data, _style in zipped
    ]


def format_cell_data(data, limit):
    """
    Change the str representation of values in data if they represent regex or
    lambda functions. Also limit the length of these strings.

    :param data: List of values to be formatted.
    :type data: ``list``
    :param limit: The number of characters allowed in each string.
    :type limit: ``int``
    :return: List of formatted and limited strings.
    :rtype: ``list``
    """
    for i, value in enumerate(data):
        if is_regex(value):
            data[i] = "REGEX('{}')".format(value.pattern)
        elif "lambda" in str(value):
            data[i] = "<lambda>"

    return _limit_cell_length(data, limit)


def _limit_cell_length(iterable, limit):
    """
    Limit the length of each string in the iterable.

    :param iterable: iterable object containing string values.
    :type iterable: ``list`` or ``tuple`` etc.
    :param limit: The number of characters allowed in each string
    :type limit: ``int``
    :return: The list of limited strings.
    :rtype: ``list`` of ``str``
    """
    return [
        val if len(str(val)) < limit else "{}...".format(str(val)[: limit - 3])
        for val in iterable
    ]


def _add_row_index(columns, rows, indices):
    """
    Add row indices as the first column to the columns and rows data.

    :param columns: List of the column names, maintains the display order.
    :type columns: ``list`` of ``str``
    :param rows: List of lists containing row data.
    :type rows: ``list`` of ``list``
    :param indices: List of row indices for each row in the table.
    :type indices: ``list`` of ``int``
    :return:
    """
    indexed_columns = ["row"] + columns
    indexed_rows = []
    for i, row in enumerate(rows):
        indexed_rows.append([indices[i]] + row)

    return indexed_columns, indexed_rows


def _create_cell_styles(colour_matrix, display_index):
    """
    Create a list of cell styles indicating whether the cell should be black,
    green or red based on whether the cell result is ignored (I), passed (P) or
    failed (F) respectively. This information is stored in the colour matrix.

    NOTE: This function expects the colour_matrix to be information on the row
    cells only, hence adding 1 to every row index to avoid the column names.
    Column cell formatting is general to every table and can be taken care of
    elsewhere.

    :param colour_matrix: A matrix listing whether each cell has passed (P),
                          failed (F) or ignored (I) which will result in the
                          cell text being green, red or black respectively. If
                          no matrix is passed all cells will be black.
    :type colour_matrix: ``list`` of ``list``
    :param display_index: Will the row indices be displayed, if so each column
                          index must be increased by 1.
    :type display_index: ``bool``
    :return: List of RowStyle objects indicating the colour of each cell.
    :rtype: ``list`` of ``testplan.common.exporters.pdf.RowStyle``
    """
    cell_styles = []
    for row_idx in range(len(colour_matrix)):
        for col_idx in range(len(colour_matrix[row_idx])):
            if colour_matrix[row_idx][col_idx] == "I":
                colour = colors.black
            elif colour_matrix[row_idx][col_idx] == "P":
                colour = colors.green
            elif colour_matrix[row_idx][col_idx] == "F":
                colour = colors.red
            col = col_idx + int(display_index)
            cell_styles.append(
                RowStyle(
                    start_column=col,
                    end_column=col,
                    start_row=row_idx + 1,
                    end_row=row_idx + 1,
                    textcolor=colour,
                )
            )
    return cell_styles


def _create_sub_table(
    columns,
    rows,
    column_start,
    column_end,
    style,
    row_indices=None,
    colour_matrix=None,
):
    """
    Create ReportLab table from a subsection of the columns and rows data using
    the column_start and column_end indices. Row indices may be added to the
    sub table if provided.

    :param columns: List of the column names, maintains the display order.
    :type columns: ``list`` of ``str``
    :param rows: List of lists containing row data.
    :type rows: ``list`` of ``list``
    :param column_start: The index of the first column to be included.
    :type column_start: ``int``
    :param column_end: The index of the last column to be included.
    :type column_end: ``int``
    :param style: The style of the ReportLab table.
    :type style: ``list`` of ``tuple``
    :param row_indices: List of row indices for each row in the table.
    :type row_indices: ``list`` of ``int``
    :param colour_matrix: A matrix listing whether each cell has passed (P),
                          failed (F) or ignored (I) which will result in the
                          cell text being green, red or black respectively. If
                          no matrix is passed all cells will be black.
    :type colour_matrix: ``list`` of ``list``
    :return: The formatted ReportLab table.
    :rtype: ``list``
    """
    # Select subsection of columns and rows.
    sub_columns = columns[column_start:column_end]
    sub_rows = [row[column_start:column_end] for row in rows]

    # If needed add row indices.
    if row_indices:
        sub_columns, sub_rows = _add_row_index(
            columns=sub_columns, rows=sub_rows, indices=row_indices
        )

    # Create the table and set it's style.
    table = Table([sub_columns] + sub_rows)

    if colour_matrix:
        colour_matrix = [row[column_start:column_end] for row in colour_matrix]
        cell_styles = _create_cell_styles(
            colour_matrix=colour_matrix, display_index=bool(row_indices)
        )
        table.setStyle(style + format_table_style(cell_styles))
    else:
        table.setStyle(style)

    return table


def create_table(
    table,
    columns,
    row_indices,
    display_index,
    max_width,
    style,
    colour_matrix=None,
):
    """
    Create a ReportLab table from a serialized entry. Table features are:

      * Cell values (rows and columns) cannot exceed the maximum number of
        characters (constanst.CELL_STRING_LENGTH). Values will stop before this
        maximum and be appended with '...'.
      * If the number of rows exceeds the maximum (constants.NUM_DISPLAYED_ROWS)
        show the first half of the allowed rows, then a row of '...', then the
        last half of the allowed rows. Also set the display_index parameter
        to True.
      * If the table is too wide to fit onto the page, split the tables columns
        into multiple rows. Also set the display_index parameter to True.

    :param table: The table containing all the data.
    :type table: ``list`` of ``dict``
    :param columns: List of the column names, maintains the display order.
    :type columns: ``list`` of ``str``
    :param row_indices: List of row indices for each row in the table.
    :type row_indices: ``list`` of ``int``
    :param display_index: If True display the row indices. This will
        automatically be set to True if the rows exceed the maximum
        allowed to display or the table is too wide (too many columns)
        to fit in a single table.
    :type display_index: ``bool``
    :param max_width: The maximum allowed width the table can be.
    :type max_width: ``int``
    :param style: The style of the ReportLab table.
    :type style: ``list`` of ``tuple``
    :param colour_matrix: A matrix listing whether each cell has passed (P),
        failed (F) or ignored (I) which will result in the cell text being
        green, red or black respectively. If no matrix is passed all cells
        will be black.
    :type colour_matrix: ``list`` of ``list``
    :return: The formatted ReportLab table.
    :rtype: ``list``
    """
    num_rows = len(table)
    num_cols = len(columns)
    display_columns = _limit_cell_length(columns, constants.CELL_STRING_LENGTH)

    # Limit the number of rows shown to X. If it goes past this show the
    # first X/2 rows, then a '...' row, then the last X/2 rows.
    if num_rows > constants.NUM_DISPLAYED_ROWS:
        display_index = True
        half_num_displayed_rows = int(constants.NUM_DISPLAYED_ROWS / 2)
        row_indices = (
            row_indices[:half_num_displayed_rows]
            + ["..."]
            + row_indices[-half_num_displayed_rows:]
        )
        table = (
            table[:half_num_displayed_rows]
            + [{col: "..." for col in columns}]
            + table[-half_num_displayed_rows:]
        )
        if colour_matrix:
            colour_matrix = (
                colour_matrix[:half_num_displayed_rows]
                + [["I"] * num_cols]
                + colour_matrix[-half_num_displayed_rows:]
            )
        num_rows = len(table)

    # Limit the values in each row to the constants.CELL_STRING_LENGTH number of
    # characters and add the '...' row if the maximum number of rows has been
    # exceeded.
    rows = [
        _limit_cell_length(
            iterable=table[i],
            limit=constants.CELL_STRING_LENGTH,
        )
        for i in range(num_rows)
    ]

    # Test if the table is too wide to fit on the page and must be split. If so
    # show the row indices.
    temp_table = _create_sub_table(
        columns=display_columns,
        rows=rows,
        column_start=0,
        column_end=num_cols,
        style=style,
    )
    if temp_table.minWidth() > max_width:
        display_index = True

    tables = []
    column_start = 0
    column_end = 1
    while column_end <= num_cols:
        # Create a table, incrementally increasing the number of columns. Show
        # the row indices if needed.
        if display_index:
            table = _create_sub_table(
                columns=display_columns,
                rows=rows,
                column_start=column_start,
                column_end=column_end,
                style=style,
                row_indices=row_indices,
                colour_matrix=colour_matrix,
            )
        else:
            table = _create_sub_table(
                columns=display_columns,
                rows=rows,
                column_start=column_start,
                column_end=column_end,
                style=style,
                colour_matrix=colour_matrix,
            )
        # If the table exceeds the max width of the page, add a table up to the
        # previous column.
        if table.minWidth() > max_width:
            table = _create_sub_table(
                columns=display_columns,
                rows=rows,
                column_start=column_start,
                column_end=column_end - 1,
                style=style,
                row_indices=row_indices,
                colour_matrix=colour_matrix,
            )
            tables.append([table, "", "", ""])
            column_start = column_end - 1
        # If we have hit the last column in the table add it to be displayed.
        elif column_end == num_cols:
            tables.append([table, "", "", ""])
            column_end += 1
        # Otherwise increment the number of columns to include.
        else:
            column_end += 1

    return tables


def format_table_style(table_styles):
    """
    Convert table style into a format ReportLab will accept.

    :param table_styles: List of RowStyle objects defining the style of the
                         ReportLab table.
    :type table_styles: ``list`` of ``testplan.common.exporters.pdf.RowStyle``
    :return: List of styles formatted into tuples.
    :rtype: ``list`` of ``tuple``
    """
    table_style = []
    for style in table_styles:
        table_style.extend(style.get_commands())
    return table_style


class RowStyle:
    """
    Helper class for managing styles for table rows.

    In Reportlab, table rows are styled using commands like:

    .. code-block:: python

      [
          (
              'BOTTOMPADDING',
              (<start_column>, <start_row>),
              (<end_column>, <end_row>),
              5
          ),
          (
              'FONT',
              (<start_column>, <start_row>),
              (<end_column>, <end_row>),
              'Helvetica',
              12
          ),
          (
              'LEFTPADDING',
              (<start_column>, <start_row>),
              (<end_column>, <end_row>),
              5
          )
      ]

    This gets messy as we have to repeat row & column indexes for
    each command. For the styling example above, the equivalent
    declaration would be:

    >>> row_style = RowStyle(
            bottom_padding=5,
            font=('Helvetica', 12),
            left_padding=5,
            start_column=<start_column>,
            end_column=<end_column>
        )

    >>> row_style.start_row = 10  # This is set by row data later
    >>> row_style.end_row = 15  # This is set by row data later
    >>> row_style.get_commands()

    Normally we'll just provide the column indexes and row
    indexes will be provided implicitly by the ``RowData`` object
    that makes use of this style.

    More info: https://www.reportlab.com/docs/reportlab-userguide.pdf
    """

    def __init__(
        self,
        start_column: int = 0,
        end_column: int = -1,
        start_row: int = None,
        end_row: int = None,
        **style_props
    ) -> None:

        if not style_props:
            raise ValueError(
                "Cannot initialize `RowStyle` without any style properties."
            )

        self._start_column = start_column
        self._end_column = end_column
        self._start_row = start_row
        self._end_row = end_row
        self._style_props = style_props

    @property
    def start_column(self) -> int:
        return self._start_column

    @property
    def end_column(self) -> int:
        return self._end_column

    @property
    def start_row(self) -> int:
        return self._start_row

    @property
    def end_row(self) -> int:
        return self._end_row

    @start_row.setter
    def start_row(self, value: int) -> None:
        if self._start_row is not None:
            raise ValueError(
                (
                    "Cannot override existing value " "for start row ({})"
                ).format(self.start_row)
            )
        self._start_row = value

    @end_row.setter
    def end_row(self, value: int) -> None:
        if self._end_row is not None:
            raise ValueError(
                ("Cannot override existing value " "for end row ({})").format(
                    self.end_row
                )
            )
        self._end_row = value

    def __repr__(self) -> str:
        tmp = (
            "{class_name}(start_column={start_column}, "
            "end_column={end_column}, start_row={start_row}, "
            "end_row={end_row}, {style_props_str})"
        )
        return tmp.format(
            class_name=self.__class__.__name__,
            start_column=self.start_column,
            end_column=self.end_column,
            start_row=self.start_row,
            end_row=self.end_row,
            style_props_str=", ".join(
                [
                    "{}={}".format(key, value)
                    for key, value in self._style_props.items()
                ]
            ),
        )

    def __eq__(self, other) -> bool:
        attrs = (
            "start_column",
            "end_column",
            "start_row",
            "end_row",
            "_style_props",
        )
        return all(getattr(self, att) == getattr(other, att) for att in attrs)

    def get_commands(self) -> tuple:
        """
        Return Reportlab compliant styling commands.

        >>> row_style = RowStyle(
          bottom_padding=5, start_column=1, end_column=3)
        >>> row_style.start_row, row_style.end_row = 10, 20
        >>> row_style.get_commands()
        (('BOTTOMPADDING', (1, 10), (3, 20), 5))
        """
        if self.start_row is None or self.end_row is None:
            raise AttributeError(
                "Cannot generate style commands unless"
                " `start_row` ({start_row}) and `end_row`"
                " ({end_row}) are set.".format(
                    start_row=self.start_row, end_row=self.end_row
                )
            )

        props = (
            (key, self._style_props[key])
            for key in sorted(self._style_props.keys())
        )

        commands = []

        # We want to skip commands with False or None values
        for key, val in props:
            if not (val is None or val is False):
                command = [
                    key.upper().replace("_", ""),
                    (self.start_column, self.start_row),
                    (self.end_column, self.end_row),
                ]
                if isinstance(val, tuple):
                    command.extend(val)
                elif not isinstance(val, bool):
                    command.append(val)
                commands.append(tuple(command))

        return tuple(commands)


class RowData:
    """
    Container object that represents one or more `Table` rows.

    Manages row index implicitly, supports custom styling
    via `RowStyle` objects.
    """

    def __init__(self, num_columns, start=0, content=None, style=None):
        self._start = start
        self.num_columns = num_columns

        self._style_objs = []
        self.content = []

        if content:
            self.append(content, style)

    def __repr__(self):
        return (
            "{class_name}(num_columns={num_columns}, start={start},"
            " content={content}, style={style_objs}".format(
                class_name=self.__class__.__name__,
                start=self.start,
                content=self.content,
                num_columns=self.num_columns,
                style_objs=self._style_objs,
            )
        )

    def __iter__(self):
        return iter(self.content)

    def __len__(self):
        return len(self.content)

    def __eq__(self, other):
        attrs = ("num_columns", "content", "_style_objs", "start", "end")
        return all(getattr(self, att) == getattr(other, att) for att in attrs)

    def __add__(self, other):
        if self.num_columns != other.num_columns:
            raise ValueError(
                "Column spans do not match ({} != {})".format(
                    self.num_columns, other.num_columns
                )
            )

        if other.start != self.end:
            raise ValueError(
                "`end` index of the first RowData must match `start`"
                " index of the second ({} != {}).".format(
                    self.end, other.start
                )
            )

        row_data = RowData(start=self.start, num_columns=self.num_columns)
        row_data.content = self.content + other.content
        row_data._style_objs = self._style_objs + other._style_objs
        return row_data

    @property
    def style(self):
        """
        Return Reportlab compatible styles (commands)
        from the RowStyle objects.
        """
        return itertools.chain.from_iterable(
            [row_style.get_commands() for row_style in self._style_objs]
        )

    @property
    def start(self):
        """Start index of the current row data."""
        return self._start

    @start.setter
    def start(self, value):
        """
        Overwrite prevention if we have existing
        `RowStyles` for this `RowData` object.
        """
        if self._style_objs:
            raise ValueError(
                "Cannot change `start` of {self}, as it would cause"
                " inconsistencies when new styles are added.".format(self=self)
            )
        self._start = value

    @property
    def end(self):
        """
        End index of the current row data, will keep
        increasing as more content is added.
        """
        return self.start + len(self)

    def append(self, content, style=None):
        """
        Append one or more rows to the current row data,
        with the given styles.

        >>> # Let's say we have 2 more rows created previously.
        >>> row_data = RowData(start=2, num_columns=4)
        >>> # # create new row data with red text.
        >>> row_data.append('hello', style=RowStyle(text_color=colors.red))
        >>> row_data.append(
                content=[
                    [
                        'first column',
                        'second column',
                        'third column',
                        'fourth column'
                    ],
                    [
                        'second line first column',
                        '',
                        '',
                        'second line fourth column']
                    ],
                style=[
                    # Applies to all columns
                    RowStyle(font=('Helvetica', 8)),
                    # Applies to last column only (0, 1, 2, [3])
                    RowStyle(text_color=colors.green, start_column=3)
                ]
            )

        :param content: Row(s) to be added.
        :type data: ``str`` or ``list`` of ``str``
            or ``list`` of ``list`` of ``str``
        :param style: Style context for the given content.
        :type style: ``RowStyle`` or ``list`` of ``RowStyle``
        :return: ``None``
        :rtype: ``NoneType``
        """
        if isinstance(content, str):
            content = [content] + [""] * (self.num_columns - 1)

        if not isinstance(content[0], (list, tuple)):
            content = [content]

        if isinstance(style, RowStyle):
            style = [style]

        if style and content:

            # Reportlab styling uses inclusive indexes on both ends
            start_row, end_row = self.end, self.end + len(content) - 1
            for style_obj in style:
                style_obj.start_row, style_obj.end_row = start_row, end_row
                self._style_objs.append(style_obj)

        # This changes `self.end`, so needs to happen last
        self.content.extend(content)
