import React, { Component } from "react";
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
import linkifyUrls from 'linkify-urls';


import FilterBox from "../Toolbar/FilterBox";
import FilterBoxPlaceholder from "../Toolbar/FilterBoxPlaceholder";
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

/**
 * Toolbar component, contains the toolbar buttons & Filter box.
 */
class Toolbar extends Component {
  constructor(props) {
    super(props);
    this.state = {
      treeView: true,
      displayTime: false,
      displayPath: false,
      filterOpen: false,
      infoModal: false,
      filter: "all",
      displayEmpty: true,
      displayTags: false,
      expandStatus: this.props.expandStatus,
    };

    this.filterOnClick = this.filterOnClick.bind(this);
    this.toggleInfoOnClick = this.toggleInfoOnClick.bind(this);
    this.toggleTreeView = this.toggleTreeView.bind(this);
    this.toggleTimeDisplay = this.toggleTimeDisplay.bind(this);
    this.togglePathDisplay = this.togglePathDisplay.bind(this);
    this.toggleEmptyDisplay = this.toggleEmptyDisplay.bind(this);
    this.toggleTagsDisplay = this.toggleTagsDisplay.bind(this);
    this.toggleFilterOnClick = this.toggleFilterOnClick.bind(this);
    this.toggleExpand = this.toggleExpand.bind(this);
    this.toggleCollapse = this.toggleCollapse.bind(this);
  }

  toggleTreeView() {
    this.props.updateTreeViewFunc(!this.state.treeView);
    this.setState(prevState => ({
      treeView: !prevState.treeView
    }));
  }

  togglePathDisplay() {
    this.props.updatePathDisplayFunc(!this.state.displayPath);
    this.setState((prevState) => ({
      displayPath: !prevState.displayPath,
    }));
  }

  toggleTimeDisplay() {
    this.props.updateTimeDisplayFunc(!this.state.displayTime);
    this.setState((prevState) => ({
      displayTime: !prevState.displayTime,
    }));
  }

  toggleInfoOnClick() {
    this.setState((prevState) => ({
      infoModal: !prevState.infoModal,
    }));
  }

  toggleFilterOnClick() {
    this.setState((prevState) => ({
      filterOpen: !prevState.filterOpen,
    }));
  }

  filterOnClick(e) {
    let checkedValue = e.currentTarget.value;
    this.setState({ filter: checkedValue });
    this.props.updateFilterFunc(checkedValue);
  }

  toggleEmptyDisplay() {
    this.props.updateEmptyDisplayFunc(!this.state.displayEmpty);
    this.setState((prevState) => ({
      displayEmpty: !prevState.displayEmpty,
    }));
  }

  toggleTagsDisplay() {
    this.props.updateTagsDisplayFunc(!this.state.displayTags);
    this.setState((prevState) => ({
      displayTags: !prevState.displayTags,
    }));
  }

  toggleExpand() {
    if (this.props.expandStatus === EXPAND_STATUS.EXPAND) {
      this.props.updateExpandStatusFunc(EXPAND_STATUS.DEFAULT);
    } else {
      this.props.updateExpandStatusFunc(EXPAND_STATUS.EXPAND);
    }
  }

  toggleCollapse() {
    if (this.props.expandStatus === EXPAND_STATUS.COLLAPSE) {
      this.props.updateExpandStatusFunc(EXPAND_STATUS.DEFAULT);
    } else {
      this.props.updateExpandStatusFunc(EXPAND_STATUS.COLLAPSE);
    }
  }

  expandButtons() {
    return (
      <>
        <NavItem key="expand-icon-item">
          <div className={css(styles.buttonsBar)}>
            <FontAwesomeIcon
              key="expand-icon"
              className={
                this.props.expandStatus === EXPAND_STATUS.EXPAND
                  ? getToggledButtonStyle(this.props.status)
                  : css(styles.toolbarButton)
              }
              icon="angle-double-down"
              onClick={this.toggleExpand}
              title="Expand all assertions"
            />
          </div>
        </NavItem>
        <NavItem key="collapse-icon-item">
          <div className={css(styles.buttonsBar)}>
            <FontAwesomeIcon
              key="collapse-icon"
              className={
                this.props.expandStatus === EXPAND_STATUS.COLLAPSE
                  ? getToggledButtonStyle(this.props.status)
                  : css(styles.toolbarButton)
              }
              icon="angle-double-up"
              onClick={this.toggleCollapse}
              title="Collapse all assertions"
            />
          </div>
        </NavItem>
      </>
    );
  }

  treeViewButton() {
    return (
      <NavItem>
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key='navigation-view'
            className={css(styles.toolbarButton)}
            icon='bars'
            title='Navigation'
            onClick={this.toggleTreeView}
          />
        </div>
      </NavItem>
    );
  }

  detailsButton(toolbarStyle) {
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
        <DropdownMenu className={css(styles.dropdown)}>
          <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
            <Label check className={css(styles.filterLabel)}>
              <Input
                type="checkbox"
                name="filter"
                value="time"
                onChange={this.toggleTimeDisplay}
              />{" "}
              Time Information
            </Label>
          </DropdownItem>
          <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
            <Label check className={css(styles.filterLabel)}>
              <Input
                type="checkbox"
                name="filter"
                value="path"
                onChange={this.togglePathDisplay}
              />{" "}
              File Path
            </Label>
          </DropdownItem>
        </DropdownMenu>
      </UncontrolledDropdown>
    );
  }

  infoButton() {
    return (
      <NavItem>
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-info"
            className={css(styles.toolbarButton)}
            icon="info"
            title="Info"
            onClick={this.toggleInfoOnClick}
          />
        </div>
      </NavItem>
    );
  }

  filterButton(toolbarStyle) {
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
                checked={this.state.filter === "all"}
                onChange={this.filterOnClick}
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
                checked={this.state.filter === "fail"}
                onChange={this.filterOnClick}
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
                checked={this.state.filter === "pass"}
                onChange={this.filterOnClick}
              />{" "}
              Passed only
            </Label>
          </DropdownItem>
          <DropdownItem divider />
          <DropdownItem toggle={false} className={css(styles.dropdownItem)}>
            <Label check className={css(styles.filterLabel)}>
              <Input
                type="checkbox"
                name="displayEmptyTest"
                checked={!this.state.displayEmpty}
                onChange={this.toggleEmptyDisplay}
              />{" "}
              Hide empty testcase
            </Label>
          </DropdownItem>
        </DropdownMenu>
      </UncontrolledDropdown>
    );
  }

  tagsButton() {
    const toolbarButtonStyle = this.state.displayTags
      ? getToggledButtonStyle(this.props.status)
      : css(styles.toolbarButton);
    const iconTooltip = this.state.displayTags ? "Hide tags" : "Display tags";

    return (
      <NavItem>
        <div className={css(styles.buttonsBar)}>
          <FontAwesomeIcon
            key="toolbar-tags"
            className={toolbarButtonStyle}
            icon="tags"
            title={iconTooltip}
            onClick={this.toggleTagsDisplay}
          />
        </div>
      </NavItem>
    );
  }

  printButton() {
    return (
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
    );
  }

  documentationButton() {
    return (
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
    );
  }

  filterBox() {
    return (
      <div
        className={css(styles.filterBox)}
        style={{
          width: this.props.filterBoxWidth,
        }}
      >
        {this.props.handleNavFilter ? (
          <FilterBox
            handleNavFilter={this.props.handleNavFilter}
            filterText={this.props.filterText}
          />
        ) : (
          <FilterBoxPlaceholder />
        )}
      </div>
    );
  }

  navbar() {
    const toolbarStyle = getToolbarStyle(this.props.status);

    return (
      <Navbar light expand="md" className={css(styles.toolbar)}>
        {this.filterBox()}
        <Collapse isOpen={this.state.isOpen} navbar className={toolbarStyle}>
          <Nav navbar className="ml-auto">
            {this.treeViewButton()}
            {this.expandButtons()}
            {this.props.extraButtons}
            {this.detailsButton(toolbarStyle)}
            {this.filterButton(toolbarStyle)}
            {this.tagsButton()}
            {this.infoButton()}
            {this.printButton()}
            {this.documentationButton()}
          </Nav>
        </Collapse>
      </Navbar>
    );
  }

  infoModal() {
    return (
      <Modal
        isOpen={this.state.infoModal}
        toggle={this.toggleInfoOnClick}
        size="lg"
        className="infoModal"
      >
        <ModalHeader toggle={this.toggleInfoOnClick}>Information</ModalHeader>
        <ModalBody>{getInfoTable(this.props.report)}</ModalBody>
        <ModalFooter>
          <Button color="light" onClick={this.toggleInfoOnClick}>
            Close
          </Button>
        </ModalFooter>
      </Modal>
    );
  }

  /**
   * Render the toolbar component.
   */
  render() {
    return (
      <div>
        {this.navbar()}
        {this.infoModal()}
      </div>
    );
  }
}

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
    const linkifyIgnore = ['user', 'command_line_string',
    'python_version', 'hostname', 'start', 'end'];


    let cell = undefined;
    if (!linkifyIgnore.includes(item[0])) {
        cell = < div dangerouslySetInnerHTML = {
            {
                __html: linkifyUrls(item[1], {
                    attributes: {
                        target: "_blank"
                    }
                })
            }
        }/>;
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
  /** Function to handle toggle of displaying tree view navigation or the default one */
  updateTreeViewFunc: PropTypes.func,
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
