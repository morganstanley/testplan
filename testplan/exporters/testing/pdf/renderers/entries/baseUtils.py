import os
import tempfile
import uuid

import matplotlib
from reportlab.lib.units import inch
from reportlab.platypus import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plot


def export_plot_to_image(graph_plot):
    """Convert a MatPlot plot into an image readable in the pdf."""
    filename = "{}.png".format(uuid.uuid4())
    temp_path = tempfile.gettempdir()
    image_pathname = os.path.join(temp_path, filename)
    graph_plot.savefig(image_pathname)
    image = Image(image_pathname)
    return image


def format_image(image):
    """Resize the image."""
    image.drawWidth = 4 * inch
    image.drawHeight = 3 * inch
    return image


def get_xy_coords(data):
    """
    Return two lists of x and y coordinates from graph data
    formatted for react-vis graphing ('x': Data, 'y': Data).
    """
    x_values = []
    y_values = []

    for coord in data:
        x_values.append(coord["x"])
        y_values.append(coord["y"])

    return x_values, y_values


def get_colour(series_options, series_name):
    """Return the graph colour for the series specified."""
    if series_options is None:
        return None
    if series_name in series_options:
        if "colour" in series_options[series_name]:
            return series_options[series_name]["colour"]
    return None


def get_axis_labels(graph_options):
    """Return the X and Y axis labels from graph options."""
    if graph_options is None:
        return None, None
    x_axis_label = None
    y_axis_label = None
    if "xAxisTitle" in graph_options:
        x_axis_label = graph_options["xAxisTitle"]
    if "yAxisTitle" in graph_options:
        y_axis_label = graph_options["yAxisTitle"]

    return x_axis_label, y_axis_label


def show_legend(graph_options):
    """Return true if the legend should be displayed."""
    if graph_options is None:
        return False
    if "legend" in graph_options:
        return graph_options["legend"]

    return False


def get_matlib_plot(source):
    """
    Call the appropriate plotting function based on
    whether a graph or chart is being plotted.
    """
    graph_type = source["graph_type"]

    valid_graph_types = [
        "Line",
        "Scatter",
        "Bar",
        "Whisker",
        "Contour",
        "Hexbin",
    ]
    valid_chart_types = ["Pie"]

    if graph_type in valid_graph_types:
        return plot_graph(source, graph_type)
    elif graph_type in valid_chart_types:
        return plot_chart(source, graph_type)
    else:
        return None


def plot_graph(source, graph_type):
    """
    Create a MatPlot plot for any graph requiring
    axis (and can therefore use the get_xy_coords function.)
    """
    data = source["graph_data"]
    graph_options = source["graph_options"]
    series_options = source["series_options"]

    # Special logic for multi-bar graph
    GROUPED_BAR_WIDTH = 0.7
    if graph_type == "Bar":
        fig, ax = plot.subplots()
        num_of_subplots = len(data)
        single_bar_width = GROUPED_BAR_WIDTH / num_of_subplots
        starting_placement = (-single_bar_width * (num_of_subplots - 1)) / 2

    for entry in data:
        colour = get_colour(series_options, entry)
        x_values, y_values = get_xy_coords(data[entry])
        if graph_type == "Line":
            plot.plot(x_values, y_values, color=colour, label=entry)
        elif graph_type == "Scatter":
            plot.scatter(x_values, y_values, color=colour, label=entry)
        elif graph_type == "Bar":
            x = list(range(len(x_values)))
            ax.bar(
                [_x + starting_placement for _x in x],
                y_values,
                single_bar_width,
                color=colour,
                label=entry,
            )
            starting_placement += single_bar_width
            ax.set_xticks(x)
            ax.set_xticklabels(x_values)
        elif graph_type == "Hexbin":
            plot.hexbin(x_values, y_values, color=colour, label=entry)
        elif graph_type == "Contour":
            plot.contour([x_values, y_values])
        elif graph_type == "Whisker":
            x_err = []
            y_err = []
            for point in data[entry]:
                x_err.append(point["xVariance"])
                y_err.append(point["yVariance"])
            plot.errorbar(
                x_values,
                y_values,
                color=colour,
                label=entry,
                xerr=x_err,
                yerr=y_err,
                fmt="x",
            )

    x_axis_label, y_axis_label = get_axis_labels(graph_options)

    if show_legend(graph_options):
        plot.legend(loc="upper left")

    plot.xlabel(x_axis_label)
    plot.ylabel(y_axis_label)

    return plot


def plot_chart(source, graph_type):
    """Create a MatPlot plot for any chart not requiring axes."""
    data = source["graph_data"]

    for entry in data:
        if graph_type == "Pie":
            angles = []
            names = []
            for coord in data[entry]:
                angles.append(coord["angle"])
                names.append(coord["name"])
            plot.pie(angles, labels=names)

    return plot
