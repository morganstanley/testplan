/**
 * Toolbar buttons used for the interactive report.
 */
import React, { useState } from "react";
import {
  NavItem,
  Modal,
  ModalHeader,
  ModalBody,
  Spinner,
  Table,
  Input,
  Label,
  Button,
  FormGroup,
} from "reactstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faSync,
  faFastBackward,
  faTimes,
  faSave,
  faPlay,
  faHourglass,
  faPowerOff,
} from "@fortawesome/free-solid-svg-icons";
import { format as dateFormat } from "date-fns";
import { css } from "aphrodite";
import axios from "axios";

import styles from "./navStyles";

const saveReportUrl = `/api/v1/interactive/report/export`;

/**
 * Render a button to trigger the report state to be reloading.
 *
 * If the reload action is currently in progress, display a spinning icon
 * instead.
 */
export const ReloadButton = (props) => {
  if (props.reloading) {
    return (
      <NavItem key="reload-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-reload"
            className={css(styles.toolbarButton, styles.toolbarInactive)}
            icon={faSync}
            title="Reloading..."
            spin
          />
        </div>
      </NavItem>
    );
  } else {
    return (
      <NavItem key="reload-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-reload"
            className={css(styles.toolbarButton)}
            icon={faSync}
            title="Reload code"
            onClick={props.reloadCbk}
          />
        </div>
      </NavItem>
    );
  }
};

/**
 * Render a button to trigger the report state to be reset.
 *
 * If the reset action is currently in progress, display an inactive icon
 * instead.
 */
export const ResetButton = (props) => {
  if (props.resetting) {
    return (
      <NavItem key="reset-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-reset"
            className={css(styles.toolbarButton, styles.toolbarInactive)}
            icon={faFastBackward}
            title="Resetting..."
          />
        </div>
      </NavItem>
    );
  } else {
    return (
      <NavItem key="reset-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-reset"
            className={css(styles.toolbarButton)}
            icon={faFastBackward}
            title="Reset plan: resets all MultiTest environments and reports"
            onClick={props.resetStateCbk}
          />
        </div>
      </NavItem>
    );
  }
};

/**
 * Render a button to abort Testpan.
 *
 * If the abort action is currently in progress, display an inactive icon
 * instead.
 */
export const AbortButton = (props) => {
  if (props.aborting) {
    return (
      <NavItem key="abort-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-abort"
            className={css(styles.toolbarButton, styles.toolbarInactive)}
            icon={faPowerOff}
            title="Aborting..."
          />
        </div>
      </NavItem>
    );
  } else {
    return (
      <NavItem key="abort-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-abort"
            className={css(styles.toolbarButton)}
            icon={faTimes}
            title="Abort Testplan"
            onClick={props.abortCbk}
          />
        </div>
      </NavItem>
    );
  }
};

/**
 * Render a button to Run all Multitests.
 *
 * If the RunAll action is currently in progress, display an inactive icon
 * instead.
 */
export const RunAllButton = (props) => {
  if (props.running) {
    return (
      <NavItem key="runall-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-runall"
            className={css(styles.toolbarButton, styles.toolbarInactive)}
            icon={faHourglass}
            title="Running tests..."
            spin
          />
        </div>
      </NavItem>
    );
  } else {
    let title;
    if (props.filter) {
      title="Run filtered tests";
    } else {
      title="Run all tests";
    }
    return (
      <NavItem key="runall-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-runall"
            className={css(styles.toolbarButton)}
            icon={faPlay}
            title={title}
            onClick={props.runAllCbk}
          />
        </div>
      </NavItem>
    );
  }
};

const getHistoryTable = (historyExporters) => {
  if (Array.isArray(historyExporters) && historyExporters.length > 0) {
    const resultList = historyExporters.map((item, i) => {
      let message;
      try {
        new URL(item.message);
        message = (
          <a href={item.message} target="_blank" rel="noopener noreferrer">
            {item.message}
          </a>
        );
      } catch (_) {
        if (item.message.split(".").pop().toLowerCase() === "pdf") {
          message = (
            <a
              href={`/api/v1/interactive/report/export/${item.uid}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {item.message}
            </a>
          );
        } else {
          message = item.message;
        }
      }
      return (
        <tr key={`exporter-${i}`}>
          <td style={{ width: "85px" }}>
            {dateFormat(new Date(item.time * 1000), "HH:mm:ss")}
          </td>
          <td style={{ width: "150px" }}>{item.name}</td>
          <td>{message}</td>
        </tr>
      );
    });

    return (
      <>
        <h5>History:</h5>
        <Table bordered responsive className={css(styles.infoTable)}>
          <tbody>{resultList}</tbody>
        </Table>
      </>
    );
  }

  return null;
};

const ModalRender = (
  exporterState,
  modalState,
  checkedExporters,
  setCheckedExporters,
  saveReport
) => {
  if (exporterState.available === undefined) {
    return (
      <div class="d-flex justify-content-center">
        <Spinner style={{ width: "3rem", height: "3rem" }} />
      </div>
    );
  }

  if (exporterState.available.length === 0) {
    return <span style={{ color: "red" }}>No exporter available</span>;
  }

  const availableExporters = exporterState.available.map((item, i) => (
    <FormGroup check>
      <Label check key={`available-exporters-${i}`}>
        <Input
          type="checkbox"
          checked={checkedExporters[item]}
          onChange={(e) => {
            setCheckedExporters((prev) => {
              const checked = { ...prev };
              checked[item] = !prev[item];
              return checked;
            });
          }}
        />{" "}
        {item}
      </Label>
    </FormGroup>
  ));

  return (
    <>
      <h5>
        Select exporters to use
        <span style={{ fontSize: "0.8em" }}>
          (check "Output" section in documentation for how-to set up more
          exporters)
        </span>
        :
      </h5>
      {availableExporters}

      <br />
      <Button
        onClick={saveReport}
        disabled={modalState.saveButtonDisable}
        color="primary"
      >
        Save
      </Button>
      <hr />
      {getHistoryTable(exporterState.history)}
    </>
  );
};

export const SaveButton = (props) => {
  const [checkedExporters, setCheckedExporters] = useState({});

  const [exporterState, setExporterState] = useState({
    available: undefined,
    history: [],
  });

  const [modalState, setModalState] = useState({
    isShow: false,
    saveButtonDisable: false,
  });

  const modalToggle = () => {
    setModalState((prev) => ({
      ...prev,
      isShow: !modalState.isShow,
    }));
  };

  const saveReport = () => {
    const exporters = Object.keys(checkedExporters).filter(
      (name) => checkedExporters[name]
    );

    if (exporters.length > 0) {
      setModalState((prev) => ({
        ...prev,
        saveButtonDisable: true,
      }));
      axios
        .post(saveReportUrl, {
          exporters: exporters,
        })
        .then((res) => {
          setExporterState((prev) => ({
            ...prev,
            history: res.data.history.reverse(),
          }));
          setModalState((prev) => ({
            ...prev,
            saveButtonDisable: false,
          }));
        })
        .catch((err) => {
          console.error(err);
          alert(err);
          setModalState((prev) => ({
            ...prev,
            saveButtonDisable: false,
          }));
        });
    } else {
      alert("Please choose an exporter");
    }
  };

  const showSaveDialog = () => {
    modalToggle();
    axios
      .get(saveReportUrl)
      .then((res) => {
        setExporterState((prev) => ({
          ...prev,
          available: res.data.available,
          history: res.data.history.reverse(),
        }));
      })
      .catch((err) => {
        console.error(err);
        alert(err);
      });
  };

  return (
    <>
      <NavItem key="save-button">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-save"
            className={css(styles.toolbarButton)}
            icon={faSave}
            title="Save report"
            onClick={showSaveDialog}
          />
        </div>
      </NavItem>
      <Modal
        isOpen={modalState.isShow}
        toggle={modalToggle}
        className="SaveModal"
        size="xl"
      >
        <ModalHeader toggle={modalToggle}>Save report</ModalHeader>
        <ModalBody>
          {ModalRender(
            exporterState,
            modalState,
            checkedExporters,
            setCheckedExporters,
            saveReport
          )}
        </ModalBody>
      </Modal>
    </>
  );
};
