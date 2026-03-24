import React, { useState } from "react";
import PropTypes from "prop-types";
import { css } from "aphrodite";
import {
  Button,
  Collapse,
  DropdownToggle,
  DropdownMenu,
  DropdownItem,
  Input,
  Label,
  Navbar,
  Nav,
  NavItem,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
  UncontrolledDropdown,
  Table,
} from "reactstrap";
import Linkify from "linkify-react";

import FilterBox from "../Toolbar/FilterBox";
import {
  STATUS,
  STATUS_CATEGORY,
  EXPAND_STATUS,
  VIEW_TYPE,
  FILTER_STATUS_GROUPS,
  FILTER_STATUSES,
} from "../Common/defaults";
import { timeToTimestamp } from "../Common/utils";

import { library } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import {
  faInfo,
  faBook,
  faPrint,
  faFilter,
  faTasks,
  faTags,
  faBars,
  faQuestionCircle,
  faAngleDoubleDown,
  faAngleDoubleUp,
  faAngleDown,
  faChartLine,
  faChartBar,
} from "@fortawesome/free-solid-svg-icons";

import styles from "./navStyles";
import {
  displayPathPreference,
  displayTimeInfoPreference,
  timeInfoUTCPreference,
  hideEmptyTestcasesPreference,
  hideSkippedTestcasesPreference,
  useTreeViewPreference,
  showStatusIconsPreference,
  mergeMultitestPartsPreference,
} from "../UserSettings/UserSettings";
import { useAtom, useAtomValue } from "jotai";
import _ from "lodash";

library.add(
  faInfo,
  faBook,
  faPrint,
  faFilter,
  faTasks,
  faTags,
  faBars,
  faQuestionCircle,
  faAngleDoubleDown,
  faAngleDoubleUp,
  faAngleDown,
  faChartLine,
  faChartBar
);

const ToolbarExpandButtons = ({
  expandStatus,
  updateExpandStatusFunc,
  status,
}) => {
  const toggleExpand = () => {
    if (expandStatus === EXPAND_STATUS.EXPAND) {
      updateExpandStatusFunc(EXPAND_STATUS.DEFAULT);
    } else {
      updateExpandStatusFunc(EXPAND_STATUS.EXPAND);
    }
  };

  const toggleCollapse = () => {
    if (expandStatus === EXPAND_STATUS.COLLAPSE) {
      updateExpandStatusFunc(EXPAND_STATUS.DEFAULT);
    } else {
      updateExpandStatusFunc(EXPAND_STATUS.COLLAPSE);
    }
  };

  return (
    <>
      <NavItem key="expand-icon-item">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="expand-icon"
            className={
              expandStatus === EXPAND_STATUS.EXPAND
                ? getToggledButtonStyle(status)
                : css(styles.toolbarButton)
            }
            icon="angle-double-down"
            onClick={toggleExpand}
            title="Expand all assertions"
          />
        </div>
      </NavItem>
      <NavItem key="collapse-icon-item">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="collapse-icon"
            className={
              expandStatus === EXPAND_STATUS.COLLAPSE
                ? getToggledButtonStyle(status)
                : css(styles.toolbarButton)
            }
            icon="angle-double-up"
            onClick={toggleCollapse}
            title="Collapse all assertions"
          />
        </div>
      </NavItem>
    </>
  );
};

const PanelSwitchIconMap = {
  [VIEW_TYPE.ASSERTION]: "chart-bar",
  [VIEW_TYPE.RESOURCE]: "chart-line",
};

const PanelViewSwitch = ({ panel_types, switchPanelViewFunc }) => {
  const onClickFunc = () => {
    const nextType =
      panel_types === VIEW_TYPE.ASSERTION
        ? VIEW_TYPE.RESOURCE
        : VIEW_TYPE.ASSERTION;
    switchPanelViewFunc(nextType);
  };

  return (
    <>
      <NavItem key="panel-swicth-icon-item">
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="panel-switch-icon"
            className={css(styles.toolbarButton)}
            icon={PanelSwitchIconMap[panel_types]}
            onClick={onClickFunc}
            title="Switch Panel View"
          />
        </div>
      </NavItem>
    </>
  );
};

const UserPreferenceCheckbox = ({ children, preferenceAtom, title }) => {
  const [preference, setPreference] = useAtom(preferenceAtom);
  return (
    <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
      <Label check className={css(styles.filterLabel)} title={title}>
        <Input
          type="checkbox"
          checked={preference}
          onChange={() => setPreference(!preference)}
        />{" "}
        {children}
      </Label>
    </DropdownItem>
  );
};

const UserPreferenceRadio = ({ children, preferenceAtom, name, value }) => {
  const [preference, setPreference] = useAtom(preferenceAtom);
  return (
    <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
      <Label
        check
        className={css(styles.filterLabel, styles.filterLabel_indent1)}
      >
        <Input
          type="radio"
          name={name}
          value={value}
          checked={value === preference}
          onChange={() => setPreference(value)}
        />{" "}
        {children}
      </Label>
    </DropdownItem>
  );
};

const TimeInfoRadioButtons = ({ enabled }) => {
  let component = enabled ? (
    <>
      <UserPreferenceRadio
        preferenceAtom={timeInfoUTCPreference}
        name="timezone"
        value={true}
      >
        UTC time
      </UserPreferenceRadio>
      <UserPreferenceRadio
        preferenceAtom={timeInfoUTCPreference}
        name="timezone"
        value={false}
      >
        Server time
      </UserPreferenceRadio>
    </>
  ) : (
    ""
  );
  return component;
};

const ToolbarPreferencesButton = ({ toolbarStyle }) => {
  return (
    <UncontrolledDropdown nav inNavbar>
      <div className={css(styles.buttonsBar)}>
        <DropdownToggle nav className={toolbarStyle}>
          <FontAwesomeIcon
            key="toolbar-details"
            icon="tasks"
            title="Preferences"
            className={css(styles.toolbarButton)}
          />
        </DropdownToggle>
      </div>
      <DropdownMenu end className={css(styles.dropdown)}>
        <DropdownItem header>Display preferences</DropdownItem>
        <UserPreferenceCheckbox preferenceAtom={displayTimeInfoPreference}>
          Display time information
        </UserPreferenceCheckbox>
        <TimeInfoRadioButtons
          enabled={useAtomValue(displayTimeInfoPreference)}
        />
        <UserPreferenceCheckbox
          preferenceAtom={displayPathPreference}
          title="You need to specify --code command line argument to use this function."
        >
          Display file path and code context
        </UserPreferenceCheckbox>
        <UserPreferenceCheckbox preferenceAtom={showStatusIconsPreference}>
          Show status icons
        </UserPreferenceCheckbox>
        <DropdownItem divider />
        <DropdownItem header>Navigation preferences</DropdownItem>
        <UserPreferenceCheckbox preferenceAtom={useTreeViewPreference}>
          Treeview navigation
        </UserPreferenceCheckbox>
        <UserPreferenceCheckbox preferenceAtom={hideEmptyTestcasesPreference}>
          Hide empty testcases
        </UserPreferenceCheckbox>
        <UserPreferenceCheckbox preferenceAtom={hideSkippedTestcasesPreference}>
          Hide skipped testcases
        </UserPreferenceCheckbox>
        <UserPreferenceCheckbox preferenceAtom={mergeMultitestPartsPreference}>
          Merge multitest parts
        </UserPreferenceCheckbox>
      </DropdownMenu>
    </UncontrolledDropdown>
  );
};

const ToolbarFilterButton = ({
  toolbarStyle,
  updateFilterFunc,
  updateEmptyDisplayFunc,
}) => {
  const [selectedStatuses, setSelectedStatuses] = useState(
    new Set(FILTER_STATUSES)
  );

  const allSelected = selectedStatuses.size === FILTER_STATUSES.length;

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedStatuses(new Set());
      updateFilterFunc([]);
    } else {
      setSelectedStatuses(new Set(FILTER_STATUSES));
      updateFilterFunc([...FILTER_STATUSES]);
    }
  };

  const toggleStatus = (status) => {
    const next = new Set(selectedStatuses);
    if (next.has(status)) {
      next.delete(status);
    } else {
      next.add(status);
    }
    setSelectedStatuses(next);
    updateFilterFunc([...next]);
  };

  return (
    <UncontrolledDropdown nav inNavbar>
      <div className={css(styles.buttonsBar)}>
        <DropdownToggle nav className={toolbarStyle}>
          <FontAwesomeIcon
            key="toolbar-filter"
            icon="filter"
            title="Choose filter"
            className={css(styles.toolbarButton)}
          />
        </DropdownToggle>
      </div>
      <DropdownMenu className={css(styles.dropdown)}>
        <DropdownItem header>Filter by status</DropdownItem>
        <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
          <Label check className={css(styles.filterLabel)}>
            <Input
              type="checkbox"
              checked={allSelected}
              onChange={toggleSelectAll}
            />{" "}
            {allSelected ? "Unselect all" : "Select all"}
          </Label>
        </DropdownItem>
        <DropdownItem divider />
        {FILTER_STATUS_GROUPS.map((group, groupIdx) => {
          const allGroupSelected = group.statuses.every((s) =>
            selectedStatuses.has(s)
          );
          const toggleGroup = () => {
            const next = new Set(selectedStatuses);
            if (allGroupSelected) {
              group.statuses.forEach((s) => next.delete(s));
            } else {
              group.statuses.forEach((s) => next.add(s));
            }
            setSelectedStatuses(next);
            updateFilterFunc([...next]);
          };
          return (
            <React.Fragment key={group.label}>
              <DropdownItem
                toggle={false}
                className={css(styles.dropdownItem)}
              >
                <Label
                  check
                  className={css(
                    styles.filterLabel,
                    styles[group.colorStyle]
                  )}
                >
                  <Input
                    type="checkbox"
                    checked={allGroupSelected}
                    onChange={toggleGroup}
                  />{" "}
                  {group.label}
                </Label>
              </DropdownItem>
              {group.statuses.length > 1 &&
                group.statuses.map((status) => (
                  <DropdownItem
                    key={status}
                    toggle={false}
                    className={css(styles.dropdownItem)}
                  >
                    <Label
                      check
                      className={css(
                        styles.filterLabel,
                        styles.filterLabel_indent2
                      )}
                    >
                      <Input
                        type="checkbox"
                        checked={selectedStatuses.has(status)}
                        onChange={() => toggleStatus(status)}
                      />{" "}
                      {status}
                    </Label>
                  </DropdownItem>
                ))}
              {groupIdx < FILTER_STATUS_GROUPS.length - 1 && (
                <DropdownItem divider />
              )}
            </React.Fragment>
          );
        })}
      </DropdownMenu>
    </UncontrolledDropdown>
  );
};

const ToolbarTagsButton = ({ status, updateTagsDisplayFunc }) => {
  const [displayTags, setDisplayTags] = useState(false);

  const toggleTagsDisplay = () => {
    updateTagsDisplayFunc(!displayTags);
    setDisplayTags(!displayTags);
  };

  const toolbarButtonStyle = displayTags
    ? getToggledButtonStyle(status)
    : css(styles.toolbarButton);
  const iconTooltip = displayTags ? "Hide tags" : "Display tags";

  return (
    <NavItem>
      <div className={css(styles.buttonsBar)}>
        <FontAwesomeIcon
          key="toolbar-tags"
          className={toolbarButtonStyle}
          icon="tags"
          title={iconTooltip}
          onClick={toggleTagsDisplay}
        />
      </div>
    </NavItem>
  );
};

/**
 * create an info button for the toolbar which show the info modal when pressed
 * @param {report} param0
 * @returns
 */
const ToolbarInfoButton = ({ report }) => {
  const [infoModal, seteInfoModal] = useState(false);

  const toggleInfoOnClick = () => {
    seteInfoModal(!infoModal);
  };

  return (
    <>
      <NavItem>
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-info"
            className={css(styles.toolbarButton)}
            icon="info"
            title="Info"
            onClick={toggleInfoOnClick}
          />
        </div>
      </NavItem>
      <Modal
        isOpen={infoModal}
        toggle={toggleInfoOnClick}
        size="lg"
        className="infoModal"
      >
        <ModalHeader toggle={toggleInfoOnClick}>Information</ModalHeader>
        <ModalBody>{getInfoTable(report)}</ModalBody>
        <ModalFooter>
          <Button color="light" onClick={toggleInfoOnClick}>
            Close
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
};

const ToolbarFilterBox = ({ filterBoxWidth, filterText, handleNavFilter }) => {
  return (
    <div
      className={css(styles.filterBox)}
      style={{
        width: filterBoxWidth,
      }}
    >
      <FilterBox handleNavFilter={handleNavFilter} filterText={filterText} />
    </div>
  );
};

/**
 * Toolbar component, contains the toolbar buttons & Filter box.
 */

const Toolbar = function (props) {
  const toolbarStyle = getToolbarStyle(props.status);

  const panelViewSwitch = props.switchPanelViewFunc ? (
    <PanelViewSwitch
      panel_types={props.current_pannel}
      switchPanelViewFunc={props.switchPanelViewFunc}
    />
  ) : null;

  return (
    <Navbar light expand="md" container={false} className={css(styles.toolbar)}>
      <ToolbarFilterBox
        filterBoxWidth={props.filterBoxWidth}
        handleNavFilter={props.handleNavFilter}
        filterText={props.filterText}
      />
      <Collapse isOpen={false} navbar className={toolbarStyle}>
        <Nav navbar className="ms-auto">
          {panelViewSwitch}
          <ToolbarExpandButtons
            expandStatus={props.expandStatus}
            updateExpandStatusFunc={props.updateExpandStatusFunc}
            status={props.status}
          />
          {props.extraButtons}
          <ToolbarPreferencesButton toolbarStyle={toolbarStyle} />
          <ToolbarFilterButton
            toolbarStyle={toolbarStyle}
            updateFilterFunc={props.updateFilterFunc}
          />
          <ToolbarTagsButton
            status={props.status}
            updateTagsDisplayFunc={props.updateTagsDisplayFunc}
          />
          <ToolbarInfoButton report={props.report} />
          <NavItem>
            <div className={css(styles.buttonsBar)}>
              <FontAwesomeIcon
                key="toolbar-print"
                className={css(styles.toolbarButton)}
                icon="print"
                title="Print page"
                onClick={window.print}
              />
            </div>
          </NavItem>
          <NavItem>
            <a
              href="http://testplan.readthedocs.io"
              rel="noopener noreferrer"
              target="_blank"
              className={css(styles.buttonsBar)}
            >
              <FontAwesomeIcon
                key="toolbar-document"
                className={css(styles.toolbarButton)}
                icon="book"
                title="Documentation"
              />
            </a>
          </NavItem>
        </Nav>
      </Collapse>
    </Navbar>
  );
};

/**
 * Get the current toolbar style based on the testplan status.
 */
const getToolbarStyle = (status) => {
  switch (STATUS_CATEGORY[status]) {
    case "passed":
      return css(styles.toolbar, styles.toolbarPassed);
    case "failed":
    case "error":
      return css(styles.toolbar, styles.toolbarFailed);
    case "unstable":
      return css(styles.toolbar, styles.toolbarUnstable);
    default:
      return css(styles.toolbar, styles.toolbarUnknown);
  }
};

/**
 * Get the current toggled toolbar button style in based on the testplan status.
 */
const getToggledButtonStyle = (status) => {
  switch (STATUS_CATEGORY[status]) {
    case "passed":
      return css(styles.toolbarButton, styles.toolbarButtonToggledPassed);
    case "failed":
    case "error":
      return css(styles.toolbarButton, styles.toolbarButtonToggledFailed);
    case "unstable":
      return css(styles.toolbarButton, styles.toolbarButtonToggledUnstable);
    default:
      return css(styles.toolbarButton, styles.toolbarButtonToggledUnknown);
  }
};

/**
 * Get the metadata from the report and render it as a table.
 */
const getInfoTable = (report) => {
  if (!report || !report.information) {
    return "No information to display.";
  }
  const infoList = report.information.map((item, i) => {
    const linkifyIgnore = [
      "user",
      "command_line_string",
      "python_version",
      "hostname",
      "runpath",
      "start",
      "end",
    ];

    let cell = undefined;
    if (!linkifyIgnore.includes(item[0])) {
      cell = (
        <Linkify as="div" options={{ target: "_blank" }}>
          {item[1]}
        </Linkify>
      );
    } else {
      cell = item[1];
    }

    return (
      <tr key={i}>
        <td className={css(styles.infoTableKey)}>{item[0]}</td>
        <td className={css(styles.infoTableValue)}>{cell}</td>
      </tr>
    );
  });

  if (!_.isEmpty(report.timer?.run)) {
    let start = timeToTimestamp(report.timer.run.at(-1).start);
    let end = timeToTimestamp(report.timer.run.at(-1).end);

    if (start) {
      infoList.push(
        <tr key="start">
          <td>start</td>
          <td>{new Date(start).toISOString()}</td>
        </tr>
      );
    }

    if (end) {
      infoList.push(
        <tr key="end">
          <td>end</td>
          <td>{new Date(end).toISOString()}</td>
        </tr>
      );
    }
  }
  return (
    <Table bordered responsive className={css(styles.infoTable)}>
      <tbody>{infoList}</tbody>
    </Table>
  );
};

Toolbar.propTypes = {
  /** Testplan report's status */
  status: PropTypes.oneOf(STATUS),
  /** Report object to display information */
  report: PropTypes.object,
  /** Additional buttons added to toolbar */
  extraButtons: PropTypes.array,
  /** Function to handle filter changing in the Filter box */
  updateFilterFunc: PropTypes.func,
  /** Function to handle toggle of displaying empty entries in the navbar */
  updateEmptyDisplayFunc: PropTypes.func,
  /** Function to handle toggle of displaying tags in the navbar */
  updateTagsDisplayFunc: PropTypes.func,
  /** Function to handle expressions entered into the Filter box */
  handleNavFilter: PropTypes.func,
  /** The global expand status */
  expandStatus: PropTypes.string,
  /** Function to handle global expand changing in the toobar */
  updateExpandStatusFunc: PropTypes.func,
  /** Current panel view type */
  current_pannel: PropTypes.string,
  /** Function to hanndle panel view switching */
  switchPanelViewFunc: PropTypes.func,
};

export default Toolbar;
export { getToggledButtonStyle };
