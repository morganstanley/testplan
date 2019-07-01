/**
 * Helper functions used to add customisability and styling to the graph and chart assertions.
 *
 */
export function getMinX(data, graph_type) {
   if(graph_type === 'Bar'){
            return 1
   }
  return data.reduce((min, p) => p.x < min ? p.x : min, data[0].y);
}

export function getMaxX(data, graph_type) {
   if(graph_type === 'Bar'){
            return 1
   }
  return data.reduce((max, p) => p.x > max ? p.x : max, data[0].y);
}


export function getMinY(data, graph_type) {
   if(graph_type === 'Bar'){
            return 1
   }
  return data.reduce((min, p) => p.y < min ? p.y : min, data[0].y);
}

export function getMaxY(data, graph_type) {
   if(graph_type === 'Bar'){
            return 1
   }
  return data.reduce((max, p) => p.y > max ? p.y : max, data[0].y);
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
