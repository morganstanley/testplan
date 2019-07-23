import os
import uuid
import tempfile
import matplotlib.pyplot as plot
import numpy as np
from reportlab.platypus import Image
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')


"""Convert a MatPlot plot into an image readable in the pdf"""
def export_plot_to_image(graph_plot):
    filename = '{0}.png'.format(uuid.uuid4())
    temp_path = tempfile.gettempdir()
    image_pathname = os.path.join(temp_path, filename)
    graph_plot.savefig(image_pathname)
    image = Image(image_pathname)
    return image


"""Resize the image"""
def format_image(image):
    image.drawWidth = 4 * inch
    image.drawHeight = 3 * inch
    return image


"""returns two lists of x and y coordinates from dictionary key by strings"""
def get_xy_coords(data):
    x_values = []
    y_values = []

    for coord in data:
        x_values.append(coord['x'])
        y_values.append(coord['y'])

    return x_values, y_values


"""returns the graph colour for the series specified"""
def get_colour(series_options, series_name):
    if series_options is None:
        return None
    if series_name in series_options:
        if 'colour' in series_options[series_name]:
            return series_options[series_name]['colour']
    return None


"""returns the axis labels from graph options"""
def get_axis_labels(graph_options):
    if graph_options is None:
        return None, None
    x_axis_label = None
    y_axis_label = None
    if 'xAxisTitle' in graph_options:
        x_axis_label = graph_options['xAxisTitle']
    if 'yAxisTitle' in graph_options:
        y_axis_label = graph_options['yAxisTitle']

    return x_axis_label, y_axis_label


"""returns whether to display the legend on the graph"""
def show_legend(graph_options):
    if graph_options is None:
        return False
    if 'legend' in graph_options:
        return graph_options['legend']

    return False


"""calls appropriate plotting function based on whether a graph or chart is being plotted"""
def get_matlib_plot(source):
    graph_type = source['graph_type']

    valid_graph_types = ['Line', 'Scatter', 'Bar', 'Whisker', 'Contour', 'Hexbin']
    valid_chart_types = ['Pie']

    if graph_type in valid_graph_types:
        return plot_graph(source, graph_type)
    elif graph_type in valid_chart_types:
        return plot_chart(source, graph_type)
    else:
        return None


"""Creates MatPlot plot for any graph requiring axis that can use get_xy_coords function"""
def plot_graph(source, graph_type):
    data = source['graph_data']
    graph_options = source['graph_options']
    series_options = source['series_options']

    # Special logic for multi-bar graph
    if graph_type is 'Bar':
        fig, ax = plot.subplots()
        num_of_subplots = len(data)
        width = 0.7/num_of_subplots
        starting_placement = (- width*(num_of_subplots - 1))/2

    for entry in data:
        colour = get_colour(series_options, entry)
        x_values, y_values = get_xy_coords(data[entry])
        if graph_type is 'Line':
            plot.plot(x_values, y_values, color=colour, label=entry)
        if graph_type is 'Scatter':
            plot.scatter(x_values, y_values, color=colour, label=entry)
        if graph_type is 'Bar':
            x = np.arange(len(x_values))
            ax.bar(x + starting_placement, y_values, width, color=colour, label=entry)
            starting_placement += width
            ax.set_xticks(x)
            ax.set_xticklabels(x_values)
        if graph_type is 'Hexbin':
            plot.hexbin(x_values, y_values, color=colour, label=entry)
        if graph_type is 'Contour':
            plot.contour([x_values, y_values])
        if graph_type is 'Whisker':
            x_err = []
            y_err = []
            for point in data[entry]:
                x_err.append(point['xVariance'])
                y_err.append(point['yVariance'])
            plot.errorbar(x_values, y_values, color=colour, label=entry, xerr=x_err, yerr=y_err, fmt='x')

    x_axis_label, y_axis_label = get_axis_labels(graph_options)

    if show_legend(graph_options):
        plot.legend(loc='upper left')

    plot.xlabel(x_axis_label)
    plot.ylabel(y_axis_label)

    return plot


"""Creates MatPlot plot for any chart not requiring axis"""
def plot_chart(source, graph_type):
    data = source['graph_data']

    for entry in data:
        if graph_type is 'Pie':
            angles = []
            names = []
            for coord in data[entry]:
                angles.append(coord['angle'])
                names.append(coord['name'])
            plot.pie(angles, labels=names)

    return plot
