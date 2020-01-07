import React, {Component} from 'react';
import PropTypes from 'prop-types';
import {StyleSheet, css} from 'aphrodite';
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
  Table
} from 'reactstrap';

import FilterBox from "../Toolbar/FilterBox";
import {GREEN, RED, ORANGE, BLACK, DARK_GREY, STATUS} from "../Common/defaults";

import {library} from '@fortawesome/fontawesome-svg-core';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';

import {
  faInfo,
  faBook,
  faPrint,
  faFilter,
  faTags,
  faQuestionCircle,
} from '@fortawesome/free-solid-svg-icons';


library.add(
  faInfo,
  faBook,
  faPrint,
  faFilter,
  faTags,
  faQuestionCircle,
);


/**
 * Toolbar component, contains the toolbar buttons & Filter box.
 */
class Toolbar extends Component {
  constructor(props) {
    super(props);
    this.state = {
      helpModal: false,
      filterOpen: false,
      infoModal: false,
      filter: 'all',
      displayEmpty: true,
      displayTags: false,
    };

    this.filterOnClick = this.filterOnClick.bind(this);
    this.toggleInfoOnClick = this.toggleInfoOnClick.bind(this);
    this.toggleEmptyDisplay = this.toggleEmptyDisplay.bind(this);
    this.toggleHelpOnClick = this.toggleHelpOnClick.bind(this);
    this.toggleTagsDisplay = this.toggleTagsDisplay.bind(this);
    this.toggleFilterOnClick = this.toggleFilterOnClick.bind(this);
  }

  toggleHelpOnClick() {
    this.setState(prevState => ({
      helpModal: !prevState.helpModal
    }));
  }

  toggleInfoOnClick() {
    this.setState(prevState => ({
      infoModal: !prevState.infoModal
    }));
  }

  toggleFilterOnClick() {
    this.setState(prevState => ({
      filterOpen: !prevState.filterOpen
    }));
  }

  filterOnClick(e){
    let checkedValue = e.currentTarget.value;
    this.setState({filter: checkedValue});
    this.props.updateFilterFunc(checkedValue);
  }

  toggleEmptyDisplay() {
    this.props.updateEmptyDisplayFunc(!this.state.displayEmpty);
    this.setState(prevState => ({
      displayEmpty: !prevState.displayEmpty
    }));
  }

  toggleTagsDisplay() {
    this.props.updateTagsDisplayFunc(!this.state.displayTags);
    this.setState(prevState => ({
      displayTags: !prevState.displayTags
    }));
  }

  printOnClick() {
    window.print();
  }

  getInfoTable(report) {
    if (report && report.information) {
      const infoList = report.information.map((item, i) => {
        return (
          <tr key={i}>
            <td className={css(styles.infoTableKey)}>{item[0]}</td>
            <td className={css(styles.infoTableValue)}>{item[1]}</td>
          </tr>
        );
      });
      if (report.timer && report.timer.run) {
        if (report.timer.run.start) {
          infoList.push(
            <tr key='start'>
              <td>start</td>
              <td>{report.timer.run.start}</td>
            </tr>
          );
        }
        if (report.timer.run.end) {
          infoList.push(
            <tr key='end'>
              <td>end</td>
              <td>{report.timer.run.end}</td>
            </tr>
          );
        }
      }
      return (
        <Table bordered responsive className={css(styles.infoTable)}>
          <tbody>
            {infoList}
          </tbody>
        </Table>
      );
    } else {
      return null;
    }
  }

  render() {
    const toolbarStyle = this.props.status === 'passed' ?
      css(styles.toolbar, styles.toolbarPassed) :
      ['failed', 'error'].includes(this.props.status) ?
        css(styles.toolbar, styles.toolbarFailed) :
        css(styles.toolbar, styles.toolbarNeutral);

    return (
      <div>
        <Navbar light expand="md" className={css(styles.toolbar)}>
          <div className={css(styles.filterBox)}>
            <FilterBox handleNavFilter={this.props.handleNavFilter}/>
          </div>
          <Collapse isOpen={this.state.isOpen} navbar className={toolbarStyle}>
            <Nav navbar className='ml-auto'>
              <NavItem>
                <div className={css(styles.buttonsBar)}>
                  <FontAwesomeIcon
                    key='toolbar-info'
                    className={css(styles.toolbarButton)}
                    icon='info'
                    title='Documentation'
                    onClick={this.toggleInfoOnClick}
                  />
                </div>
              </NavItem>
              <UncontrolledDropdown nav inNavbar>
                <div className={css(styles.buttonsBar)}>
                  <DropdownToggle nav className={toolbarStyle}>
                    <FontAwesomeIcon
                      key='toolbar-filter'
                      icon='filter'
                      title='Choose filter'
                      className={css(styles.toolbarButton)}
                    />
                  </DropdownToggle>
                </div>
                <DropdownMenu className={css(styles.filterDropdown)}>
                  <DropdownItem toggle={false}
                    className={css(styles.dropdownItem)}>
                    <Label check className={css(styles.filterLabel)}>
                      <Input type="radio" name="filter" value='all'
                        checked={this.state.filter === 'all'}
                        onChange={this.filterOnClick}/>{' '}
                      All
                    </Label>
                  </DropdownItem>
                  <DropdownItem toggle={false}
                    className={css(styles.dropdownItem)}>
                    <Label check className={css(styles.filterLabel)}>
                      <Input type="radio" name="filter" value='fail'
                        checked={this.state.filter === 'fail'}
                        onChange={this.filterOnClick}/>{' '}
                      Failed only
                    </Label>
                  </DropdownItem>
                  <DropdownItem toggle={false}
                    className={css(styles.dropdownItem)}>
                    <Label check className={css(styles.filterLabel)}>
                      <Input type="radio" name="filter" value='pass'
                        checked={this.state.filter === 'pass'}
                        onChange={this.filterOnClick}/>{' '}
                      Passed only
                    </Label>
                  </DropdownItem>
                  <DropdownItem divider />
                  <DropdownItem toggle={false}
                    className={css(styles.dropdownItem)}>
                    <Label check className={css(styles.filterLabel)}>
                      <Input type="checkbox" name="displayEmptyTest"
                        checked={!this.state.displayEmpty}
                        onChange={this.toggleEmptyDisplay}/>{' '}
                      Hide empty testcase
                    </Label>
                  </DropdownItem>
                </DropdownMenu>
              </UncontrolledDropdown>
              <NavItem>
                <div className={css(styles.buttonsBar)}>
                  <FontAwesomeIcon
                    key='toolbar-print'
                    className={css(styles.toolbarButton)}
                    icon='print'
                    title='Print page'
                    onClick={this.printOnClick}
                  />
                </div>
              </NavItem>
              <NavItem>
                <div className={css(styles.buttonsBar)}>
                  <FontAwesomeIcon
                    key='toolbar-tags'
                    className={css(styles.toolbarButton)}
                    icon='tags'
                    title='Toggle tags'
                    onClick={this.toggleTagsDisplay}
                  />
                </div>
              </NavItem>
              <NavItem>
                <div className={css(styles.buttonsBar)}>
                  <FontAwesomeIcon
                    key='toolbar-question'
                    className={css(styles.toolbarButton)}
                    icon='question-circle'
                    title='Help'
                    onClick={this.toggleHelpOnClick}
                  />
                </div>
              </NavItem>
              <NavItem>
                <a href='http://testplan.readthedocs.io'
                  rel='noopener noreferrer' target='_blank'
                  className={css(styles.buttonsBar)}>
                  <FontAwesomeIcon
                    key='toolbar-document'
                    className={css(styles.toolbarButton)}
                    icon='book'
                    title='Documentation'
                  />
                </a>
              </NavItem>
            </Nav>
          </Collapse>
        </Navbar>
        <Modal
            isOpen={this.state.helpModal}
            toggle={this.toggleHelpOnClick}
            className='HelpModal'
          >
            <ModalHeader toggle={this.toggleHelpOnClick}>Help</ModalHeader>
            <ModalBody>
              This is filter box help!
            </ModalBody>
            <ModalFooter>
              <Button color="light" onClick={this.toggleHelpOnClick}>
                Close
              </Button>
            </ModalFooter>
          </Modal>
          <Modal
            isOpen={this.state.infoModal}
            toggle={this.toggleInfoOnClick}
            size='lg'
            className='infoModal'
          >
            <ModalHeader toggle={this.toggleInfoOnClick}>
              Information
            </ModalHeader>
            <ModalBody>
              {this.getInfoTable(this.props.report)}
            </ModalBody>
            <ModalFooter>
              <Button color="light" onClick={this.toggleInfoOnClick}>
                Close
              </Button>
            </ModalFooter>
          </Modal>
      </div>
    );
  }
}

Toolbar.propTypes = {
  /** Testplan report's status */
  status: PropTypes.oneOf(STATUS),
  /** Report object to display information */
  report: PropTypes.object,
  /** Function to handle filter changing in the Filter box */
  updateFilterFunc: PropTypes.func,
  /** Function to handle toggle of displaying empty entries in the navbar */
  updateEmptyDisplayFunc: PropTypes.func,
  /** Function to handle toggle of displaying tags in the navbar */
  updateTagsDisplayFunc: PropTypes.func,
  /** Function to handle expressions entered into the Filter box */
  handleNavFilter: PropTypes.func,
};

const styles = StyleSheet.create({
  toolbar: {
    padding: '0',
  },

  filterBox: {
    float: 'left',
    height: '100%',
  },
  buttonsBar: {
    float: 'left',
    height: '100%',
    color: 'white',
  },
  filterLabel: {
    width: '100%',
    display: 'inlinde-block',
    cursor: 'pointer',
    padding: '0.2em',
    'margin-left': '2em',
  },
  dropdownItem: {
    padding: '0',
    ':focus': {
      outline: '0',
    },
  },
  toolbarButton: {
    textDecoration: 'none',
    position: 'relative',
    display: 'inline-block',
    height: '2.4em',
    width: '2.4em',
    cursor: 'pointer',
    color: 'white',
    padding: '0.7em 0em 0.7em 0em',
    transition: 'all 0.3s ease-out 0s',
    ':hover': {
        color: DARK_GREY
    }
  },
  toolbarUnstable: {
    backgroundColor: ORANGE,
    color: 'white'
  },
  toolbarUnknown: {
    backgroundColor: BLACK,
    color: 'white'
  },
  toolbarPassed: {
    backgroundColor: GREEN,
    color: 'white'
  },
  toolbarFailed: {
    backgroundColor: RED,
    color: 'white'
  },
  filterDropdown: {
    'margin-top': '-0.3em'
  },
  infoTable: {
    'table-layout': 'fixed',
    width: '100%'
  },
  infoTableKey: {
    width: '25%',
  },
  infoTableValue: {
    'word-wrap': 'break-word',
    'overflow-wrap': 'break-word',
  }
});

export default Toolbar;
