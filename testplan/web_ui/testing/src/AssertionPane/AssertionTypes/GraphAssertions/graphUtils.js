/**
 * Helper functions used to add customisability and styling to the graph and chart assertions.
 *
 */

 function checkDataIsEmpty(data){
    if(data.length === 0){
     throw "No data inputted to graph";
   }
 }

export function getMinX(data, graph_type) {
   checkDataIsEmpty(data)
   switch(graph_type){
        case 'Bar':
            return 1;
        default:
            return data.reduce((min, p) => p.x < min ? p.x : min);
   }
}

export function getMaxX(data, graph_type) {
   checkDataIsEmpty(data)
   switch(graph_type){
        case 'Whisker':
            return data.reduce((max, p) => (p.x + p.xVariance) > max ? (p.x + p.xVariance) : max);
        case 'Bar':
            return 1;
        default:
            return data.reduce((max, p) => p.x > max ? p.x : max);
   }
}

export function getMinY(data, graph_type) {
   checkDataIsEmpty(data)
   switch(graph_type){
        case 'Bar':
            return 1;
        default:
            return data.reduce((min, p) => p.y < min ? p.y : min);
   }
}

export function getMaxY(data, graph_type) {
   checkDataIsEmpty(data)
   switch(graph_type){
        case 'Whisker':
            return data.reduce((max, p) => (p.y + p.yVariance) > max ? (p.y + p.yVariance) : max);
        case 'Bar':
            return 1;
        default:
            return data.reduce((max, p) => p.y > max ? p.y : max);
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
