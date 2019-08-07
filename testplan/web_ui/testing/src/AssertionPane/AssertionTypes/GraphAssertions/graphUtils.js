/**
 * Helper functions used to add customisability and styling to the graph and chart assertions.
 */

/**
 * Return the JSX for the 'style' parameter for the graph component
 * to help render nicer graphs, not currently set by the user
 */
export function returnStyle(graph_type){
    if(graph_type === 'Contour'){
       return(
                {
                    stroke: '#125C77',
                    strokeLinejoin: 'round'
                }
        );
    }
}

/**
 * Return the JSX for the 'XType' parameter for the XYPlot
 * component to be make the x axis increment either numerical or ordinal
 */
export function returnXType(graph_type){
    if(graph_type ==='Bar'){
       return("ordinal");
    }
}

const COLOUR_PALETTE=['#1c5c9c', '#68caea', '#7448c5', '#633836',
                      '#485051', '#336a85', '#94b1c5', '#ababab']
/**
 * Return the colours for every series, given the series_options. Each series'
 * colour assigned depending on whether the user has specified an option,
 * otherwise return from a colour scheme/palette, then random colours
 * (tinted darker/blue)
 */
export function returnColour(series_options, data){
    let series_colours = {};
    let colour_options = COLOUR_PALETTE.slice(0);

    for(let series_key in data){
        //Assign colour from user specified options if possible
        if(series_options != null){
            if(series_options[series_key]!= null){
                if(series_options[series_key].colour!= null){
                    series_colours[series_key] =
                        series_options[series_key].colour;
                    continue;
                }
            }
        }

        //Otherwise choose next colour available from colour palette
        if(colour_options.length !== 0){
             let colour = colour_options[0];
             series_colours[series_key] = colour;
             colour_options.shift();
        }
        //Otherwise if no more available colours, choose random colour
        else{
            let colour = '';
            for (let i = 0; i < 4; i++) {
             colour += (Math.round(Math.random() * 15)).toString(16);
            }
            for (let i = 0; i < 2; i++) {
             colour += (10+ Math.round(Math.random() * 5)).toString(16);
            }
            series_colours[series_key] = colour;
        }
    }
    return series_colours;
}

/**
 * Return an xAxisTitle for the graph component
 * or nothing if it has not been set
 */
export function returnXAxisTitle(graph_options){
    if(graph_options == null){
        return;
    }
    if(graph_options.xAxisTitle !== null){
        return graph_options.xAxisTitle;
    }
}

/**
 * Return an yAxisTitle for the graph component
 * or nothing if it has not been set
 */
export function returnYAxisTitle(graph_options){
    if(graph_options == null){
        return;
    }
    if(graph_options.yAxisTitle !== null){
        return graph_options.yAxisTitle;
    }
}