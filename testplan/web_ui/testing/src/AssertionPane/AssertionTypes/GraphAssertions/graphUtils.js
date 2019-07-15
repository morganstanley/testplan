/**
 * Helper functions used to add customisability and styling to the graph and chart assertions.
 *
 */

 function checkDataIsEmpty(data){
    if(data.length === 0){
     throw "No data inputted to graph";
   }
 }

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

export function returnRadius(graph_type){
    if(graph_type === 'Hexbin'){
       return(10);
    }
}

export function returnXType(graph_type){
    if(graph_type ==='Bar'){
       return("ordinal");
    }
}

export function returnColour(options){
    if(options == null){
        return '#' + (Math.random().toString(16) + "000000").substring(2,8);
    }
    if(options.colour !== null){
        return options.colour;
    }
}

export function returnXAxisTitle(graph_options){
    if(graph_options == null){
        return;
    }
    if(graph_options.xAxisTitle !== null){
        return graph_options.xAxisTitle;
    }
}

export function returnYAxisTitle(graph_options){
    if(graph_options == null){
        return;
    }
    if(graph_options.yAxisTitle !== null){
        return graph_options.yAxisTitle;
    }
}