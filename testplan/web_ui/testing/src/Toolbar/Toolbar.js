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
import { STATUS, STATUS_CATEGORY, EXPAND_STATUS } from "../Common/defaults";

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
} from "@fortawesome/free-solid-svg-icons";

import styles from "./navStyles";
import {
  displayPathPreference,
  displayTimeInfoPreference,
  hideEmptyTestcasesPreference,
  hideSkippedTestcasesPreference,
  useTreeViewPreference,
} from "../UserSettings/UserSettings";
import { useAtom } from "jotai";

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
  faAngleDown
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

const UserPreferenceCheckbox = ({ children, preferenceAtom }) => {
  const [preference, setPreference] = useAtom(preferenceAtom);
  return (
    <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
      <Label check className={css(styles.filterLabel)}>
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

const ToolbarPreferencesButton = ({ toolbarStyle }) => {
  return (
    <UncontrolledDropdown nav inNavbar>
      <div className={css(styles.buttonsBar)}>
        <DropdownToggle nav className={toolbarStyle}>
          <FontAwesomeIcon
            key="toolbar-details"
            icon="tasks"
            title="Choose details"
            className={css(styles.toolbarButton)}
          />
        </DropdownToggle>
      </div>
      <DropdownMenu right className={css(styles.dropdown)}>
        <DropdownItem header>Display preferences</DropdownItem>
        <UserPreferenceCheckbox preferenceAtom={displayTimeInfoPreference}>
          Display time information
        </UserPreferenceCheckbox>
        <UserPreferenceCheckbox preferenceAtom={displayPathPreference}>
          Display file path for assertions
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
      </DropdownMenu>
    </UncontrolledDropdown>
  );
};

const ToolbarFilterButton = ({
  toolbarStyle,
  updateFilterFunc,
  updateEmptyDisplayFunc,
}) => {
  const [filter, setFilter] = useState("all");

  const filterOnClick = (e) => {
    let checkedValue = e.currentTarget.value;
    updateFilterFunc(checkedValue);
    setFilter(checkedValue);
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
        <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
          <Label check className={css(styles.filterLabel)}>
            <Input
              type="radio"
              name="filter"
              value="all"
              checked={filter === "all"}
              onChange={filterOnClick}
            />{" "}
            All
          </Label>
        </DropdownItem>
        <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
          <Label check className={css(styles.filterLabel)}>
            <Input
              type="radio"
              name="filter"
              value="fail"
              checked={filter === "fail"}
              onChange={filterOnClick}
            />{" "}
            Failed only
          </Label>
        </DropdownItem>
        <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
          <Label check className={css(styles.filterLabel)}>
            <Input
              type="radio"
              name="filter"
              value="pass"
              checked={filter === "pass"}
              onChange={filterOnClick}
            />{" "}
            Passed only
          </Label>
        </DropdownItem>
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

  return (
    <Navbar light expand="md" className={css(styles.toolbar)}>
      <ToolbarFilterBox
        filterBoxWidth={props.filterBoxWidth}
        handleNavFilter={props.handleNavFilter}
        filterText={props.filterText}
      />
      <Collapse isOpen={false} navbar className={toolbarStyle}>
        <Nav navbar className="ml-auto">
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
  if (report.timer && report.timer.run) {
    if (report.timer.run.start) {
      infoList.push(
        <tr key="start">
          <td>start</td>
          <td>{report.timer.run.start}</td>
        </tr>
      );
    }
    if (report.timer.run.end) {
      infoList.push(
        <tr key="end">
          <td>end</td>
          <td>{report.timer.run.end}</td>
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
};

export default Toolbar;
export { getToggledButtonStyle };
