import React, { useState, useEffect, useLayoutEffect } from "react";
import axios from "axios";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LineElement,
  LinearScale,
  PointElement,
  TimeSeriesScale,
  Filler,
} from "chart.js";
import { format as dateFormat, addMinutes as dateAddMinutes } from "date-fns";
import { Line } from "react-chartjs-2";
import annotationPlugin from "chartjs-plugin-annotation";
import "chartjs-adapter-date-fns";
import _ from "lodash";
import PropTypes from "prop-types";
import prettyBytes from "pretty-bytes";
import { getResourceUrl } from "../Common/utils";
import {
  RED,
  BLUE,
  DARK_BLUE,
  TEAL,
  DARK_TEAL,
  YELLOW,
  DARK_YELLOW,
  ROSE,
  DARK_ROSE,
} from "../Common/defaults";

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  Filler,
  CategoryScale,
  LineElement,
  LinearScale,
  PointElement,
  TimeSeriesScale,
  annotationPlugin
);

const percentageTicks = () => {
  return {
    format: {
      style: "percent",
    },
  };
};

const defaultTicks = () => {
  return {
    format: {
      style: "decimal",
    },
  };
};

const prettySizeTicks = (options) => {
  return {
    callback: (val, index) => {
      return prettyBytes(val, options);
    },
  };
};

const ResourceGraph = ({
  data,
  label,
  startTime,
  endTime,
  valueTicks,
  lineColor,
  fillColor,
  cap,
}) => {
  const ticks = valueTicks();
  const ticksCallback = ticks.callback;
  const annotation = cap
    ? {
        annotations: {
          total: {
            type: "line",
            yMin: cap,
            yMax: cap,
            borderColor: "rgb(255, 99, 132)",
            borderWidth: 2,
          },
        },
      }
    : {};
  const tickInterval = data.length > 10 ? Math.ceil(data.length / 10) : 1;
  const timezoneOffset = new Date().getTimezoneOffset();
  return (
    <div
      style={{
        position: "relative",
        height: "150px",
        width: "100%",
      }}
    >
      <Line
        width="100%"
        height="150"
        data={{
          datasets: [
            {
              fill: true,
              data: data,
              borderColor: lineColor,
              backgroundColor: fillColor,
              label: label,
            },
          ],
        }}
        options={{
          maintainAspectRatio: false,
          responsive: true,
          elements: {
            point: {
              radius: 0,
            },
          },
          interaction: {
            intersect: false,
            mode: "index",
          },
          animation: {
            duration: 0, // disable animation
          },
          scales: {
            x: {
              type: "timeseries",
              min: startTime,
              max: endTime,
              ticks: {
                callback: (value, index) => {
                  if (index % tickInterval === 0) {
                    return `${dateFormat(
                      dateAddMinutes(value, timezoneOffset),
                      "H:mm:ss"
                    )} (UTC)`;
                  }
                  return null;
                },
              },
            },
            y: {
              ticks: ticks,
              beginAtZero: true,
            },
          },
          plugins: {
            tooltip: {
              animation: false,
              callbacks: {
                title: (context) => {
                  return `${dateFormat(
                    dateAddMinutes(context[0].raw.x, timezoneOffset),
                    "H:mm:ss"
                  )} (UTC)`;
                },
                label: (context) => {
                  if (ticksCallback) {
                    return `${label}: ${ticksCallback(context.raw.y)}`;
                  } else {
                    return `${label}: ${context.formattedValue}`;
                  }
                },
              },
            },
            annotation: annotation,
          },
        }}
      />
    </div>
  );
};

ResourceGraph.propTypes = {
  data: PropTypes.array,
  label: PropTypes.string,
  startTime: PropTypes.number,
  endTime: PropTypes.number,
  valueTicks: PropTypes.func,
  lineColor: PropTypes.string,
  fillColor: PropTypes.string,
};

const HostResourceGraphContainer = ({
  time,
  cpu,
  memory,
  disk,
  iops,
  startTime,
  endTime,
  memorySize,
}) => {
  const cpuData = [];
  const memoryData = [];
  const diskData = [];
  const iopsData = [];

  for (let t in time) {
    cpuData.push({ x: time[t] * 1000, y: cpu[t] / 100 });
    memoryData.push({ x: time[t] * 1000, y: memory[t] });
    diskData.push({ x: time[t] * 1000, y: disk[t] });
    iopsData.push({
      x: time[t] * 1000,
      y: iops[t],
    });
  }

  const cpuGraph = (
    <ResourceGraph
      data={cpuData}
      label="CPU"
      startTime={startTime}
      endTime={endTime}
      valueTicks={percentageTicks}
      lineColor={DARK_BLUE}
      fillColor={BLUE}
    />
  );
  const memoryGraph = (
    <ResourceGraph
      data={memoryData}
      label="Memory"
      startTime={startTime}
      endTime={endTime}
      valueTicks={() => {
        return prettySizeTicks({ binary: true });
      }}
      lineColor={DARK_TEAL}
      fillColor={TEAL}
      cap={memorySize}
    />
  );
  const diskGraph = (
    <ResourceGraph
      data={diskData}
      label="Disk"
      startTime={startTime}
      endTime={endTime}
      valueTicks={prettySizeTicks}
      lineColor={DARK_YELLOW}
      fillColor={YELLOW}
    />
  );

  const iopsGraph = (
    <ResourceGraph
      data={iopsData}
      label="IOPS"
      startTime={startTime}
      endTime={endTime}
      valueTicks={defaultTicks}
      lineColor={DARK_ROSE}
      fillColor={ROSE}
    />
  );

  return (
    <>
      {cpuGraph}
      {memoryGraph}
      {diskGraph}
      {iopsGraph}
    </>
  );
};

const HostMetaTitle = ({
  uid,
  onClick,
  hostname,
  cpuCount,
  diskSize,
  diskPath,
  memorySize,
  isLocal,
}) => {
  let uidDiv = null;
  if (isLocal) {
    uidDiv = (
      <span style={{ marginLeft: "5px", fontSize: "10px", color: "gray" }}>
        LocalHost
      </span>
    );
  } else if (hostname !== uid) {
    uidDiv = (
      <span style={{ marginLeft: "5px", fontSize: "10px", color: "gray" }}>
        {uid}
      </span>
    );
  }

  return (
    <div
      style={{ width: "100%", textAlign: "left", cursor: "pointer" }}
      id={`resource-host-${uid}`}
      onClick={onClick}
    >
      <div style={{ fontSize: "24px" }}>
        {hostname}
        {uidDiv}
      </div>
      <div style={{ fontSize: "12px", color: "gray" }}>
        CPU: {cpuCount * 100}% Memory Size:{" "}
        {prettyBytes(memorySize, { binary: true })} Disk Size:{" "}
        {prettyBytes(diskSize)} Disk Path: {diskPath}
      </div>
    </div>
  );
};

HostMetaTitle.propTypes = {
  uid: PropTypes.string,
  onClick: PropTypes.func,
  hostname: PropTypes.string,
  cpuCount: PropTypes.number,
  diskSize: PropTypes.number,
  diskPath: PropTypes.string,
  memorySize: PropTypes.number,
  isLocal: PropTypes.bool,
};

const HostResource = ({
  metadata,
  resource_meta_path,
  startTime,
  endTime,
  isOpen,
  onClick,
  entryIndex,
}) => {
  const [hostResourceGraph, setHostResourceGraph] = useState(null);
  const [errorInfo, setErrorInfo] = useState(null);

  useLayoutEffect(() => {
    if (_.isEmpty(metadata.resource_file)) {
      setHostResourceGraph(<div>No Resource Data</div>);
    } else {
      const hostResourceUrl = getResourceUrl(
        resource_meta_path,
        metadata.resource_file
      );
      axios
        .get(hostResourceUrl)
        .then((response) => {
          setHostResourceGraph(
            <HostResourceGraphContainer
              {...response.data}
              startTime={startTime}
              endTime={endTime}
              memorySize={metadata.memory_size}
            />
          );
        })
        .catch((error) => {
          console.error(error);
          setErrorInfo(error.message);
        });
    }
  }, [resource_meta_path, metadata, startTime, endTime]);

  if (errorInfo) {
    return <span style={{ color: { RED } }}>{errorInfo}</span>;
  } else {
    return (
      <div
        style={{
          padding: "20px 40px",
          marginBottom: "10px",
          backgroundColor: "#f8f9fa",
          borderRadius: "4px",
        }}
        id={entryIndex}
      >
        <HostMetaTitle
          onClick={onClick}
          key={metadata.uid}
          uid={metadata.uid}
          hostname={metadata.hostname}
          cpuCount={metadata.cpu_count}
          diskSize={metadata.disk_size}
          diskPath={metadata.disk_path}
          memorySize={metadata.memory_size}
          isLocal={metadata.is_local}
        />
        <div style={{ display: isOpen ? "block" : "none" }}>
          {hostResourceGraph}
        </div>
      </div>
    );
  }
};

HostResource.propTypes = {
  metadata: PropTypes.object,
  startTime: PropTypes.number,
  endTime: PropTypes.number,
  isOpen: PropTypes.bool,
  onClick: PropTypes.func,
};

const TopUsageBanner = ({
  maxCPU,
  maxMemory,
  maxDisk,
  maxIOPS,
  onClickCallBack,
}) => {
  const itemStyle = {
    padding: "8px",
    border: "1px solid #0597ff",
    backgroundColor: "#e5f0f9",
    borderRadius: "2px",
    color: "#115598",
    fontSize: "14px",
    fontWeight: "500",
    cursor: "pointer",
  };
  const cpuDiv = _.isEmpty(maxCPU?.value, true) ? null : (
    <div
      style={itemStyle}
      title={maxCPU.uid}
      onClick={onClickCallBack(maxCPU.uid)}
    >
      Max CPU Usage: {maxCPU.value}%
    </div>
  );

  const memDiv = _.isEmpty(maxMemory?.value, true) ? null : (
    <div
      style={itemStyle}
      title={maxMemory.uid}
      onClick={onClickCallBack(maxMemory.uid)}
    >
      Max Memory Usage: {prettyBytes(maxMemory.value, { binary: true })}
    </div>
  );

  const diskDiv = _.isEmpty(maxDisk?.value, true) ? null : (
    <div
      style={itemStyle}
      title={maxDisk.uid}
      onClick={onClickCallBack(maxDisk.uid)}
    >
      Max Disk Usage: {prettyBytes(maxDisk.value)}
    </div>
  );

  const iopsDiv = _.isEmpty(maxIOPS?.value, true) ? null : (
    <div
      style={itemStyle}
      title={maxIOPS.uid}
      onClick={onClickCallBack(maxIOPS.uid)}
    >
      Max IOPS: {maxIOPS.value.toFixed(2)}
    </div>
  );
  return (
    <div
      style={{
        width: "100%",
        gap: "8px",
        display: "flex",
      }}
    >
      {cpuDiv}
      {memDiv}
      {diskDiv}
      {iopsDiv}
    </div>
  );
};

const TopResourceShap = {
  value: PropTypes.number,
  uid: PropTypes.string,
};

TopUsageBanner.propTypes = {
  maxCPU: PropTypes.shape(TopResourceShap),
  maxMemory: PropTypes.shape(TopResourceShap),
  maxDisk: PropTypes.shape(TopResourceShap),
  maxIOPS: PropTypes.shape(TopResourceShap),
  onClickCallBack: PropTypes.func,
};

const maxVal = (meta, key, maxRef) => {
  if (maxRef.value === undefined || meta[key] > maxRef.value) {
    maxRef.value = meta[key];
    maxRef.uid = meta.uid;
  }
};

const ResourceContainer = ({
  defaultExpandStatus,
  defaultJumpHostUid,
  resource_meta_path,
  hostMeta,
  testStartTime,
  testEndTime,
}) => {
  const [graphState, setGraphState] = useState({
    jumpHostUid: defaultJumpHostUid,
    expendHost: defaultExpandStatus,
  });
  const [isJumped, setIsJumped] = useState(false);
  const entryPrefix = "hostEntry";
  useEffect(() => {
    if (isJumped === false) {
      for (let [index, ele] of hostMeta.entries()) {
        if (ele.uid === graphState.jumpHostUid) {
          setIsJumped(true);
          setTimeout(() => {
            document
              .querySelector(`#${entryPrefix}${index}`)
              ?.scrollIntoView(true);
          }, 100);

          break;
        }
      }
    }
  }, [hostMeta, graphState.jumpHostUid, isJumped]);

  const updateExpandStatus = (hostUid) => {
    return () => {
      if (graphState.expendHost[hostUid] === true) {
        setGraphState((prev) => {
          const newState = { ...prev };
          newState.expendHost = { ...prev.expendHost, ...{ [hostUid]: false } };
          return newState;
        });
      } else {
        setGraphState((prev) => {
          const newState = { ...prev };
          newState.expendHost = { ...prev.expendHost, ...{ [hostUid]: true } };
          return newState;
        });
      }
    };
  };

  const jumpToHost = (hostUid) => {
    return () => {
      setGraphState((prev) => {
        const newState = { ...prev };
        newState.jumpHostUid = hostUid;
        newState.expendHost = { ...prev.expendHost, ...{ [hostUid]: true } };
        return newState;
      });
      setIsJumped(false);
    };
  };

  const hostEnties = [];
  const maxCPU = {};
  const maxMemory = {};
  const maxDisk = {};
  const maxIOPS = {};

  hostMeta.forEach((hostValue, index) => {
    maxVal(hostValue, "max_cpu", maxCPU);
    maxVal(hostValue, "max_memory", maxMemory);
    maxVal(hostValue, "max_disk", maxDisk);
    maxVal(hostValue, "max_iops", maxIOPS);
    hostEnties.push(
      <HostResource
        key={hostValue.uid}
        entryIndex={`${entryPrefix}${index}`}
        isOpen={graphState.expendHost[hostValue.uid] === true}
        resource_meta_path={resource_meta_path}
        onClick={updateExpandStatus(hostValue.uid)}
        metadata={hostValue}
        startTime={testStartTime}
        endTime={testEndTime}
      />
    );
  });

  const usageBanner = (
    <TopUsageBanner
      maxCPU={maxCPU}
      maxMemory={maxMemory}
      maxDisk={maxDisk}
      maxIOPS={maxIOPS}
      onClickCallBack={jumpToHost}
    />
  );

  return (
    <>
      {usageBanner}
      <div
        key="panel-blank-header-margin"
        style={{ height: "20px", width: "100%" }}
      ></div>
      {hostEnties}
    </>
  );
};

ResourceContainer.propTypes = {
  defaultExpandStatus: PropTypes.object,
  defaultJumpHostUid: PropTypes.string,
  resource_meta_path: PropTypes.string,
  hostMeta: PropTypes.array,
  testStartTime: PropTypes.number,
  testEndTime: PropTypes.number,
};

/**
 * Render the Resource monitor and event data.
 */
const ResourcePanel = ({ report, selectedHostUid }) => {
  const [resourceMeta, setResourceMeta] = useState(null);
  const [errorInfo, setErrorInfo] = useState(null);

  useEffect(() => {
    if (_.isEmpty(report.resource_meta_path) || resourceMeta) {
      return;
    } else {
      const resourceUrl = getResourceUrl(report.resource_meta_path);
      axios
        .get(resourceUrl)
        .then((response) => {
          setResourceMeta(response.data);
        })
        .catch((error) => {
          console.error(error);
          setErrorInfo(error.message);
        });
    }
  }, [resourceMeta, report]);

  let content = null;
  if (_.isEmpty(report.resource_meta_path)) {
    content = <div>No Resource data</div>;
  } else if (errorInfo) {
    content = <div style={{ color: { RED } }}>{errorInfo}</div>;
  } else if (resourceMeta) {
    const hostMeta = resourceMeta.entries;
    const testStartTime = Number(new Date(report.timer.run.start));
    const testEndTime = Number(new Date(report.timer.run.end));
    const defaultExpandStatus = selectedHostUid
      ? { [selectedHostUid]: true }
      : {};
    content = (
      <ResourceContainer
        key={`resource-container${new Date()}`}
        defaultExpandStatus={defaultExpandStatus}
        defaultJumpHostUid={selectedHostUid}
        resource_meta_path={report.resource_meta_path}
        hostMeta={hostMeta}
        testStartTime={testStartTime}
        testEndTime={testEndTime}
      />
    );
  } else {
    content = <div>Loading</div>;
  }

  return (
    <div
      style={{
        padding: "20px",
        flex: "1",
        overflowY: "auto",
        minWidth: "800px",
      }}
    >
      {content}
    </div>
  );
};

ResourcePanel.propTypes = {
  report: PropTypes.object,
  selectedHostUid: PropTypes.string,
};

export default ResourcePanel;
