import React, { useState, useEffect } from "react";
import { useRouteMatch } from "react-router-dom";
import axios from "axios";
import {
  Chart as ChartJS,
  ArcElement,
  BarElement,
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
import { Line, Bar } from "react-chartjs-2";
import annotationPlugin from "chartjs-plugin-annotation";
import "chartjs-adapter-date-fns";
import _ from "lodash";
import PropTypes from "prop-types";
import prettyBytes from "pretty-bytes";
import { getResourceUrl, timeToTimestamp } from "../Common/utils";
import {
  RED,
  GREEN,
  BLUE,
  DARK_BLUE,
  TEAL,
  DARK_TEAL,
  YELLOW,
  DARK_YELLOW,
  ROSE,
  DARK_ROSE,
  LOCALHOST,
  STATUS_CATEGORY,
} from "../Common/defaults";

ChartJS.register(
  ArcElement,
  BarElement,
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

const hostEntryPrefix = "hostEntry";
const anchorPrefix = "anchor";

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

const AnchorDiv = ({ elementIds }) => {
  const anchorDiv = [];
  for (let uid of elementIds) {
    anchorDiv.push(<div key={uid} id={`${anchorPrefix}${uid}`}></div>);
  }
  return anchorDiv;
};

AnchorDiv.propTypes = {
  elementIds: PropTypes.array,
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
                    )}Z`;
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
                  )}Z`;
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

const TimerGraph = ({ timerEntries, startTime, endTime }) => {
  const labels = [];
  const timezoneOffset = new Date().getTimezoneOffset();
  const datasets = [
    {
      data: [],
      backgroundColor: [],
      barThickness: 6,
      minBarLength: 2,
    },
  ];

  timerEntries.forEach((entity) => {
    labels.push(entity.name);
    datasets[0].backgroundColor.push(
      // TODO: move color to a constant map
      entity.status === STATUS_CATEGORY.passed ? GREEN : RED
    );
    let start = null;
    if (!_.isNil(entity.timer[0].setup?.start)) {
      start = entity.timer[0].setup.start;
    } else if (!_.isNil(entity.timer[0].run?.start)) {
      start = entity.timer[0].run.start;
    } else {
      datasets[0].data.push(null);
      return;
    }

    if (!_.isNil(entity.timer[0].teardown?.end)) {
      datasets[0].data.push([start, entity.timer[0].teardown.end]);
    } else if (!_.isNil(entity.timer[0].run?.end)) {
      datasets[0].data.push([start, entity.timer[0].run.end]);
    } else {
      datasets[0].data.push(null);
    }
  });
  const height = 10 + timerEntries.length * 5;
  return (
    <div
      style={{
        width: "100%",
      }}
    >
      <Bar
        height={height}
        options={{
          indexAxis: "y",
          responsive: true,
          animation: {
            duration: 0, // disable animation
          },
          scales: {
            x: {
              type: "time",
              beginAtZero: false,
              min: startTime,
              max: endTime,
              time: {
                unit: "second",
              },
              ticks: {
                autoSkip: false,
                maxTicksLimit: 10,
                callback: (value, index) => {
                  return `${dateFormat(
                    dateAddMinutes(value, timezoneOffset),
                    "H:mm:ss"
                  )}Z`;
                },
              },
            },
            y: {
              ticks: {
                autoSkip: false,
              },
            },
          },
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  return [
                    `From: ${dateFormat(
                      dateAddMinutes(context.raw[0], timezoneOffset),
                      "H:mm:ss"
                    )}Z`,
                    `To: ${dateFormat(
                      dateAddMinutes(context.raw[1], timezoneOffset),
                      "H:mm:ss"
                    )}Z`,
                    `Duration: ${(
                      (context.raw[1] - context.raw[0]) /
                      1000
                    ).toFixed(2)}s`,
                  ];
                },
              },
            },
          },
        }}
        data={{
          labels: labels,
          datasets: datasets,
        }}
      />
    </div>
  );
};

TimerGraph.propTypes = {
  timerEntries: PropTypes.array,
  startTime: PropTypes.number,
  endTime: PropTypes.number,
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
      <>
        {hostname}
        <span style={{ marginLeft: "5px", fontSize: "10px", color: "gray" }}>
          {LOCALHOST}
        </span>
      </>
    );
  } else if (hostname !== uid) {
    uidDiv = (
      <>
        {hostname}
        <span style={{ marginLeft: "5px", fontSize: "10px", color: "gray" }}>
          {uid}
        </span>
      </>
    );
  } else {
    uidDiv = <>{hostname}</>;
  }
  const cpuInfo = _.isNil(cpuCount) ? null : (
    <span>CPU: {cpuCount * 100}%</span>
  );
  const memoryInfo = _.isNil(memorySize) ? null : (
    <span>Memory Size: {prettyBytes(memorySize, { binary: true })}</span>
  );
  const diskInfo = _.isNil(diskSize) ? null : (
    <span>Disk Size: {prettyBytes(diskSize)}</span>
  );
  const diskPathInfo = _.isNil(diskPath) ? null : (
    <span>Disk Path: {diskPath}</span>
  );
  return (
    <div
      style={{ width: "100%", textAlign: "left" }}
      id={`resource-host-${uid}`}
    >
      <div style={{ fontSize: "24px" }}>{uidDiv}</div>
      <div style={{ fontSize: "12px", color: "gray" }}>
        {cpuInfo} {memoryInfo} {diskInfo} {diskPathInfo}
      </div>
    </div>
  );
};

HostMetaTitle.propTypes = {
  uid: PropTypes.string,
  hostname: PropTypes.string,
  cpuCount: PropTypes.number,
  diskSize: PropTypes.number,
  diskPath: PropTypes.string,
  memorySize: PropTypes.number,
  isLocal: PropTypes.bool,
};

const HostResource = ({
  entryTag,
  resourceMetaPath,
  resourceEntry,
  startTime,
  endTime,
}) => {
  const [hostResourceGraph, setHostResourceGraph] = useState(null);

  useEffect(() => {
    if (_.isEmpty(resourceEntry.metaData.resource_file)) {
      setHostResourceGraph(<>{null}</>);
    } else {
      const hostResourceUrl = getResourceUrl(
        resourceMetaPath,
        resourceEntry.metaData.resource_file
      );
      axios
        .get(hostResourceUrl)
        .then((response) => {
          setHostResourceGraph(
            <>
              <HostResourceGraphContainer
                {...response.data}
                startTime={startTime}
                endTime={endTime}
                memorySize={resourceEntry.memory_size}
              />
            </>
          );
        })
        .catch((error) => {
          console.error(error);
          setHostResourceGraph(<div>{error.message}</div>);
        });
    }
  }, [resourceMetaPath, resourceEntry, startTime, endTime]);

  let timerGraph = undefined;
  let anchorDiv = undefined;
  if (!_.isNil(resourceEntry.timer)) {
    anchorDiv = (
      <AnchorDiv elementIds={resourceEntry.timer.map((e) => e.uid)} />
    );

    timerGraph = (
      <TimerGraph
        timerEntries={resourceEntry.timer}
        startTime={startTime}
        endTime={endTime}
      />
    );
  }

  return (
    <div
      style={{
        padding: "20px 40px",
        marginBottom: "10px",
        backgroundColor: "#f8f9fa",
        borderRadius: "4px",
        width: "100%",
      }}
      id={entryTag}
    >
      {anchorDiv}
      <HostMetaTitle
        uid={resourceEntry.metaData.uid}
        hostname={resourceEntry.metaData.hostname}
        cpuCount={resourceEntry.metaData.cpu_count}
        diskSize={resourceEntry.metaData.disk_size}
        diskPath={resourceEntry.metaData.disk_path}
        memorySize={resourceEntry.metaData.memory_size}
        isLocal={resourceEntry.metaData.is_local}
      />
      {hostResourceGraph}
      {timerGraph}
    </div>
  );
};

HostResource.propTypes = {
  entryTag: PropTypes.string,
  resourceMetaPath: PropTypes.string,
  resourceEntry: PropTypes.object,
  startTime: PropTypes.number,
  endTime: PropTypes.number,
};

const TopUsageBanner = ({ maxCPU, maxMemory, maxDisk, maxIOPS }) => {
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
  const cpuDiv = _.isNil(maxCPU?.value, true) ? null : (
    <div style={itemStyle} title={maxCPU.uid}>
      Max CPU Usage: {maxCPU.value}%
    </div>
  );

  const memDiv = _.isNil(maxMemory?.value) ? null : (
    <div style={itemStyle} title={maxMemory.uid}>
      Max Memory Usage: {prettyBytes(maxMemory.value, { binary: true })}
    </div>
  );

  const diskDiv = _.isNil(maxDisk?.value) ? null : (
    <div style={itemStyle} title={maxDisk.uid}>
      Max Disk Usage: {prettyBytes(maxDisk.value)}
    </div>
  );

  const iopsDiv = _.isNil(maxIOPS?.value) ? null : (
    <div style={itemStyle} title={maxIOPS.uid}>
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

const maxVal = (meta, maxRef, hostTag) => {
  const keyMap = {
    max_cpu: "maxCPU",
    max_memory: "maxMemory",
    max_disk: "maxDisk",
    max_iops: "maxIOPS",
  };
  for (let key in keyMap) {
    if (maxRef[keyMap[key]] === undefined) {
      maxRef[keyMap[key]] = {};
    }

    if (
      maxRef[keyMap[key]].value === undefined ||
      meta[key] > maxRef[keyMap[key]].value
    ) {
      maxRef[keyMap[key]].value = meta[key];
      maxRef[keyMap[key]].tag = hostTag;
    }
  }
};

const ResourceContainer = ({
  resourceMetaPath,
  resourceEntries,
  timerEntries,
  testStartTime,
  testEndTime,
}) => {
  const routeMatch = useRouteMatch();

  useEffect(() => {
    const selection = routeMatch.params?.selection;
    if (selection) {
      const selectedDiv = document.getElementById(
        `${anchorPrefix}${selection}`
      );
      if (selectedDiv) {
        selectedDiv.scrollIntoView({ hehavior: "smooth", block: "start" });
      }
    }
  }, [routeMatch]);

  let usageBanner;
  const hostContent = [];
  let hostIndex = 0;

  if (!_.isEmpty(resourceEntries)) {
    const maxRes = {};

    for (let host in resourceEntries) {
      hostIndex++;
      const hostMeta = resourceEntries[host].metaData;
      const hostTag = `${hostEntryPrefix}${hostIndex}`;
      maxVal(hostMeta, maxRes, hostTag);
      const hostDiv = (
        <HostResource
          key={hostMeta.uid}
          entryTag={hostTag}
          resourceMetaPath={resourceMetaPath}
          resourceEntry={resourceEntries[host]}
          startTime={testStartTime}
          endTime={testEndTime}
        />
      );
      if (host === LOCALHOST) {
        hostContent.unshift(hostDiv); // insert to first
      } else {
        hostContent.push(hostDiv);
      }
    }
    if (!_.isEmpty(maxRes)) {
      usageBanner = <TopUsageBanner {...maxRes} />;
    }
  }

  const timerContent = [];
  if (!_.isEmpty(timerEntries)) {
    for (let hostId in timerEntries) {
      hostIndex++;
      const hostTag = `${hostEntryPrefix}${hostIndex}`;
      timerContent.push(
        <HostResource
          key={hostId}
          entryTag={hostTag}
          resourceMetaPath={null}
          resourceEntry={{
            metaData: { uid: hostId },
            timer: timerEntries[hostId],
          }}
          startTime={testStartTime}
          endTime={testEndTime}
        />
      );
    }
  }

  return (
    <>
      {usageBanner}
      <div
        key="panel-blank-header-margin"
        style={{ height: "20px", width: "100%" }}
      ></div>
      {hostContent}
      {timerContent}
    </>
  );
};

ResourceContainer.propTypes = {
  resourceMetaPath: PropTypes.string,
  resourceEntries: PropTypes.object,
  timerEntries: PropTypes.object,
  testStartTime: PropTypes.number,
  testEndTime: PropTypes.number,
};

const normalizeTimer = (timer) => {
  let timerArray = [];
  if (Array.isArray(timer?.run)) {
    for (let timerIndex in timer.run) {
      timerArray.push({
        setup: {
          start: timeToTimestamp(timer.setup[timerIndex]?.start),
          end: timeToTimestamp(timer.setup[timerIndex]?.end),
        },
        run: {
          start: timeToTimestamp(timer.run[timerIndex]?.start),
          end: timeToTimestamp(timer.run[timerIndex]?.end),
        },
        teardown: {
          start: timeToTimestamp(timer.teardown[timerIndex]?.start),
          end: timeToTimestamp(timer.teardown[timerIndex]?.end),
        },
      });
    }
  } else {
    timerArray.push({
      setup: {
        start: timeToTimestamp(timer.setup?.start),
        end: timeToTimestamp(timer.setup?.end),
      },
      run: {
        start: timeToTimestamp(timer.run?.start),
        end: timeToTimestamp(timer.run?.end),
      },
      teardown: {
        start: timeToTimestamp(timer.teardown?.start),
        end: timeToTimestamp(timer.teardown?.end),
      },
    });
  }
  return timerArray;
};

const extractTimeInfo = (report) => {
  const timeInfo = {};
  if (Array.isArray(report.entries)) {
    for (let mtIndex in report.entries) {
      const timer = normalizeTimer(report.entries[mtIndex].timer);
      let host = report.entries[mtIndex].host
        ? report.entries[mtIndex].host
        : LOCALHOST;
      if (_.isNil(timeInfo[host])) {
        timeInfo[host] = [];
      }
      timeInfo[host].push({
        name: report.entries[mtIndex].name,
        uid: report.entries[mtIndex].uid,
        status: report.entries[mtIndex].status,
        timer: timer,
      });
    }
  }
  return timeInfo;
};

/**
 * Render the Resource monitor and event data.
 */
const ResourcePanel = ({ report }) => {
  const [resourceMeta, setResourceMeta] = useState(null);
  const [errorInfo, setErrorInfo] = useState(null);

  useEffect(() => {
    if (resourceMeta || errorInfo) {
      return;
    }

    const timerEntries = extractTimeInfo(report);

    if (_.isEmpty(report.resource_meta_path)) {
      setResourceMeta({
        resourceEntries: null,
        timerEntries: timerEntries,
      });
      return;
    } else {
      const resourceUrl = getResourceUrl(report.resource_meta_path);
      axios
        .get(resourceUrl)
        .then((response) => {
          const resourceEntries = {};
          for (let resourceIndex in response.data.entries) {
            const hostEntry = response.data.entries[resourceIndex];
            if (hostEntry.is_local && !_.isNil(timerEntries[LOCALHOST])) {
              resourceEntries[LOCALHOST] = {
                metaData: hostEntry,
                timer: timerEntries[LOCALHOST],
              };
              delete timerEntries[LOCALHOST];
            } else if (!_.isNil(timerEntries[hostEntry.uid])) {
              resourceEntries[hostEntry.uid] = {
                metaData: hostEntry,
                timer: timerEntries[hostEntry.uid],
              };
              delete timerEntries[hostEntry.uid];
            }
          }

          setResourceMeta({
            resourceEntries: resourceEntries,
            timerEntries: timerEntries,
          });
        })
        .catch((error) => {
          console.error(error);
          setErrorInfo(error.message);
        });
    }
  }, [resourceMeta, report, errorInfo]);

  let content = null;

  if (errorInfo) {
    content = <div style={{ color: { RED } }}>{errorInfo}</div>;
  } else if (_.isEmpty(resourceMeta)) {
    content = <div>Resource data was not collected for this test report.</div>;
  } else if (resourceMeta) {
    const { resourceEntries, timerEntries } = resourceMeta;
    const testStartTime = Array.isArray(report.timer.run)
      ? new Date(report.timer.run[0].start).getTime()
      : new Date(report.timer.run.start).getTime();
    const testEndTime = Array.isArray(report.timer.run)
      ? new Date(report.timer.run[0].end).getTime()
      : new Date(report.timer.run.end).getTime();

    content = (
      <ResourceContainer
        key={`resource-container`}
        resourceMetaPath={report.resource_meta_path}
        resourceEntries={resourceEntries}
        timerEntries={timerEntries}
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
};

export default ResourcePanel;
