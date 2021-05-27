import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import axios from "axios";
import Plot from "react-plotly.js";
import CircularProgress from "@material-ui/core/CircularProgress";
import { makeStyles } from "@material-ui/core/styles";
import { getAttachmentUrl } from "../../Common/utils";
import { GREEN, RED } from "../../Common/defaults";

const useStyle = makeStyles({
  circular: {
    color: GREEN,
  },
});

export default function PlotlyAssertion(props) {
  const [plotlyData, setPlotlyData] = useState(null);
  const [errorInfo, setErrorInfo] = useState(null);
  const styles = useStyle();
  const dataUrl = getAttachmentUrl(props.assertion.dst_path, props.reportUid);

  useEffect(() => {
    axios
      .get(dataUrl)
      .then((response) => {
        setPlotlyData(response.data);
      })
      .catch((error) => {
        setErrorInfo(error);
      });
  }, [dataUrl]);

  if (plotlyData) {
    return (
      <Plot
        data={plotlyData.data}
        layout={plotlyData.layout}
        useResizeHandler={true}
        style={props.assertion.style || { width: "100%" }}
      />
    );
  } else if (errorInfo) {
    return <span style={{ color: { RED } }}>{errorInfo}</span>;
  } else {
    return (
      <div>
        <CircularProgress className={styles.circular} />
      </div>
    );
  }
}

PlotlyAssertion.prototype = {
  /** Assertion being rendered */
  assertion: PropTypes.object,
};
