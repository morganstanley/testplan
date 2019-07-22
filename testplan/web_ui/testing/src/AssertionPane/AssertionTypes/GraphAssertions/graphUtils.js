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

/**
 * Return a colour for the graph component depending on whether the user has
 * specified an option, otherwise return random colour (tinted with blue)
 */
export function returnColour(options){
    if(options == null){
        let colour = '';
        for (let i = 0; i < 4; i++) {
         colour += (Math.round(Math.random() * 15)).toString(16);
        }
        for (let i = 0; i < 2; i++) {
         colour += (10+ Math.round(Math.random() * 5)).toString(16);;
        }
        return '#' + (colour)
    }
    if(options.colour !== null){
        return options.colour;
    }
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