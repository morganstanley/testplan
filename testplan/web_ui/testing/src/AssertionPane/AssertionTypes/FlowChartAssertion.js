import React, { useEffect } from "react";
import PropTypes from "prop-types";
import Dagre from "@dagrejs/dagre";
import ReactFlow, {
    useNodesState,
    useEdgesState,
    getBezierPath,
    EdgeLabelRenderer,
    BaseEdge,
    MarkerType
} from "reactflow";
import "reactflow/dist/style.css";
import { truncateString } from "../../Common/utils";

// Helper component to render edge label
function EdgeLabel({ transform, label }) {
  return (
    <div
      style={{
        position: 'absolute',
        background: 'transparent',
        padding: 10,
        color: '#000000',
        fontSize: 12,
        fontWeight: 700,
        transform,
      }}
      className="nodrag nopan"
    >
        {label}
    </div>
  );
};

const customEdge = ({
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    data,
    selected,
    markerEnd
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge id={id} markerEnd={markerEnd} path={edgePath}/>
      <EdgeLabelRenderer>
        {selected && data.startLabel && (
            <EdgeLabel
              transform={`translate(-50%, -40%) translate(${sourceX}px,${sourceY}px)`}
              label={data.startLabel}
            />
        )}
        {data.label && (
            <EdgeLabel
              transform={`translate(-50%, -50%) translate(${labelX}px,${labelY}px)`}
              label={selected ? data.label : truncateString(data.label)}
            />
        )}
        {selected && data.endLabel && (
            <EdgeLabel
              transform={`translate(-50%, -60%) translate(${targetX}px,${targetY}px)`}
              label={data.endLabel}
            />
        )}
      </EdgeLabelRenderer>
    </>
  );
};

const edgeTypes = {
    custom: customEdge,
};

const dagreGraph = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
dagreGraph.setGraph({});

const getLayoutedElements = (nodes, edges) => {
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {width: 150, height: 40});
  });
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  Dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = "top";
    node.sourcePosition = "bottom";

    node.position = {
        x: nodeWithPosition.x - 150 / 2,
        y: nodeWithPosition.y - 40 / 2,
    };
  });
  return { nodes, edges };
};

export default function FlowChartAssertion(props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const assertion_nodes = props.assertion.nodes;
  const assertion_edges = props.assertion.edges;
  useEffect(() => {
    const initialNodes = assertion_nodes;
    const initialEdges = assertion_edges.map((edge) => ({
      type: "custom",
      data: {
        startLabel: edge.startLabel,
        label: edge.label,
        endLabel: edge.endLabel
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        height: "20",
        width: "20",
      },
      ...edge
    }));
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      initialNodes,
      initialEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  },
  // eslint-disable-next-line
  []);

  return (
    <div style={{ width: '100%', height: 800 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        edgeTypes={edgeTypes}
        fitView
      />
    </div>
  );
}

FlowChartAssertion.prototype = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
