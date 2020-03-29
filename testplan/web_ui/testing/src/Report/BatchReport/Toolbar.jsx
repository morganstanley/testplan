import React, { useMemo } from 'react';
import { css } from 'aphrodite';
import {
  Button, Collapse, DropdownToggle, DropdownMenu, DropdownItem, Input, Label,
  Navbar, Nav, NavItem, Modal, ModalHeader, ModalBody, ModalFooter, Table,
  UncontrolledDropdown,
} from 'reactstrap';
import { library } from '@fortawesome/fontawesome-svg-core';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faInfo, faBook, faPrint, faFilter, faTags, faQuestionCircle,
} from '@fortawesome/free-solid-svg-icons';

import FilterBox from '../../Toolbar/FilterBox';
import { STATUS_CATEGORY } from '../../Common/defaults';
import { default as navStyles } from '../../Toolbar/navStyles';
import { filterStates, useAppState } from './state';

library.add(faInfo, faBook, faPrint, faFilter, faTags, faQuestionCircle);

/** @typedef {any|string|number|boolean|null|symbol|BigInt} ActuallyAny */
/** @typedef {keyof typeof STATUS_CATEGORY} StatusType */

/**
 * Get the current toolbar style based on the testplan status.
 * @param {StatusType} [status]
 * @returns {ReturnType<typeof css>}
 */
const getToolbarStyle = (status) => css(navStyles.toolbar, {
  passed: navStyles.toolbarPassed,
  failed: navStyles.toolbarFailed,
  error: navStyles.toolbarFailed,
  unstable: navStyles.toolbarUnstable,
}[STATUS_CATEGORY[status]] || navStyles.toolbarUnknown);

/**
 * Get the metadata from the report and render it as a table.
 * @returns {React.FunctionComponentElement}
 */
function InfoTable() {
  const [ jsonReport ] = useAppState('app.reports.batch.jsonReport', false);
  return useMemo(() => {
    if(!(jsonReport && jsonReport.information)) {
      return (
        <table>
          <tbody>
            <tr>
              <td>No information to display.</td>
            </tr>
          </tbody>
        </table>
      );
    }
    const infoList = jsonReport.information.map((item, i) => (
      <tr key={i.toString()}>
        <td className={css(navStyles.infoTableKey)}>{item[0]}</td>
        <td className={css(navStyles.infoTableValue)}>{item[1]}</td>
      </tr>
    ));
    if(jsonReport.timer && jsonReport.timer.run) {
      if(jsonReport.timer.run.start) {
        infoList.push(
          <tr key='start'>
            <td>start</td>
            <td>{jsonReport.timer.run.start}</td>
          </tr>
        );
      }
      if(jsonReport.timer.run.end) {
        infoList.push(
          <tr key='end'>
            <td>end</td>
            <td>{jsonReport.timer.run.end}</td>
          </tr>
        );
      }
    }
    return (
      <Table bordered responsive={true} className={css(navStyles.infoTable)}>
        <tbody>
          {infoList}
        </tbody>
      </Table>
    );
  }, [ jsonReport ]);
}

/**
 * Return the button which links to the documentation.
 * @returns {React.FunctionComponentElement}
 */
function DocumentationButton() {
  const [ docURL ] = useAppState('documentation.url.external', false);
  return (
    <NavItem>
      <a href={docURL}
         rel='noopener noreferrer'
         target='_blank'
         className={css(navStyles.buttonsBar)}
      >
        <FontAwesomeIcon key='toolbar-document'
                         className={css(navStyles.toolbarButton)}
                         icon='book'
                         title='Documentation'
        />
      </a>
    </NavItem>
  );
}

/**
 * Return the button which toggles the help modal.
 * @returns {React.FunctionComponentElement}
 */
function HelpButton() {
  const [ isShowHelpModal, setShowHelpModal ] = useAppState(
    'app.reports.batch.isShowHelpModal',
    'setAppBatchReportShowHelpModal'
  );
  return useMemo(() => (
    <NavItem>
      <div className={css(navStyles.buttonsBar)}>
        <span onClick={() => setShowHelpModal(!isShowHelpModal)}>
          <FontAwesomeIcon key='toolbar-question'
                           className={css(navStyles.toolbarButton)}
                           icon='question-circle'
                           title='Help'
          />
        </span>
      </div>
    </NavItem>
  ), [ isShowHelpModal, setShowHelpModal ]);
}

/**
 * Return the button which toggles the display of tags.
 * @returns {React.FunctionComponentElement}
 */
function TagsButton() {
  const [ isShowTags, setShowTags ] = useAppState(
    'app.reports.batch.isShowTags',
    'setAppBatchReportIsShowTags'
  );
  return (
    <NavItem>
      <div className={css(navStyles.buttonsBar)}>
        <span onClick={() => setShowTags(!isShowTags)}>
          <FontAwesomeIcon key='toolbar-tags'
                           icon='tags'
                           title='Toggle tags'
                           className={css(navStyles.toolbarButton)}
          />
        </span>
      </div>
    </NavItem>
  );

}

/**
 * Buttons used to set the filters
 * @param {Object} obj
 * @param {string} obj.value
 * @param {string} obj.label
 * @returns {React.FunctionComponentElement}
 */
function FilterRadioButton({ value, label }) {
  const [ filter, setFilter ] = useAppState(
    'app.reports.batch.filter',
    'setAppBatchReportFilter'
  );
  return (
    <DropdownItem toggle={false} className={css(navStyles.dropdownItem)}>
      <Label check className={css(navStyles.filterLabel)}>
        <Input type='radio'
               name='filter'
               value={value}
               checked={filter === value}
               onChange={evt => setFilter(evt.currentTarget.value)}
        />
        {' ' + label}
      </Label>
    </DropdownItem>
  );
}

/**
 * Checkbox that determines whether empty testcases are shown
 * @param {React.PropsWithoutRef<{label: string}>} props
 * @returns {React.FunctionComponentElement}
 */
function DisplayEmptyCheckBox({ label }) {
  const [ isDisplayEmpty, setDisplayEmpty ] = useAppState(
    'app.reports.batch.isDisplayEmpty',
    'setAppBatchReportIsDisplayEmpty'
  );
  return (
    <DropdownItem toggle={false} className={css(navStyles.dropdownItem)}>
      <Label check className={css(navStyles.filterLabel)}>
        <Input type='checkbox'
               name='displayEmpty'
               checked={!isDisplayEmpty}
               onChange={() => setDisplayEmpty(!isDisplayEmpty)}
        />
        {' ' + label}
      </Label>
    </DropdownItem>
  );
}

/**
 * Return the button which prints the current testplan.
 * @returns {React.FunctionComponentElement}
 */
const PrintButton = () => (
  <NavItem>
    <div className={css(navStyles.buttonsBar)}>
      <span onClick={window.print}>
        <FontAwesomeIcon key='toolbar-print'
                         className={css(navStyles.toolbarButton)}
                         icon='print'
                         title='Print page'
        />
      </span>
    </div>
  </NavItem>
);

/**
 * Return the filter button which opens a drop-down menu.
 * @param {React.PropsWithoutRef<{toolbarStyle: string}>} props
 * @returns {React.FunctionComponentElement}
 */
const FilterButton = ({ toolbarStyle }) => (
  <UncontrolledDropdown nav inNavbar>
    <div className={css(navStyles.buttonsBar)}>
      <DropdownToggle nav className={toolbarStyle}>
        <FontAwesomeIcon key='toolbar-filter'
                         icon='filter'
                         title='Choose filter'
                         className={css(navStyles.toolbarButton)}
        />
      </DropdownToggle>
    </div>
    <DropdownMenu className={css(navStyles.filterDropdown)}>
      <FilterRadioButton value={filterStates.ALL} label='All' />
      <FilterRadioButton value={filterStates.FAILED} label='Failed only' />
      <FilterRadioButton value={filterStates.PASSED} label='Passed only' />
      <DropdownItem divider />
      <DisplayEmptyCheckBox label='Hide empty testcase' />
    </DropdownMenu>
  </UncontrolledDropdown>
);

/**
 * Return the info button which toggles the info modal.
 * @returns {React.FunctionComponentElement}
 */
function InfoButton() {
  const [ isShowInfoModal, setShowInfoModal ] = useAppState(
    'app.reports.batch.isShowInfoModal',
    'setAppBatchReportShowInfoModal'
  );
  return (
    <NavItem>
      <div className={css(navStyles.buttonsBar)}>
        <span onClick={() => setShowInfoModal(!isShowInfoModal)}>
          <FontAwesomeIcon key='toolbar-info'
                           className={css(navStyles.toolbarButton)}
                           icon='info'
                           title='Info'
          />
        </span>
      </div>
    </NavItem>
  );
}

/**
 * Return the information modal.
 * @returns {React.FunctionComponentElement}
 */
function InfoModal() {
  const [ isShowInfoModal, setShowInfoModal ] = useAppState(
    'app.reports.batch.isShowInfoModal',
    'setAppBatchReportShowInfoModal'
  );
  const toggle = () => setShowInfoModal(!isShowInfoModal);
  return (
    <Modal isOpen={isShowInfoModal}
           toggle={toggle}
           size='lg'
           className='infoModal'
    >
      <ModalHeader toggle={toggle}>
        Information
      </ModalHeader>
      <ModalBody>
        <InfoTable />
      </ModalBody>
      <ModalFooter>
        <Button color='light' onClick={toggle}>
          Close
        </Button>
      </ModalFooter>
    </Modal>
  );
}

/**
 * Return the help modal.
 * @returns {React.FunctionComponentElement}
 */
function HelpModal() {
  const [ isShowHelpModal, setShowHelpModal ] = useAppState(
    'app.reports.batch.isShowHelpModal',
    'setAppBatchReportShowHelpModal'
  );
  const toggle = () => setShowHelpModal(!isShowHelpModal);
  return (
    <Modal isOpen={isShowHelpModal} toggle={toggle} className='HelpModal'>
      <ModalHeader toggle={toggle}>
        Help
      </ModalHeader>
      <ModalBody>
        This is filter box help!
      </ModalBody>
      <ModalFooter>
        <Button color='light' onClick={toggle}>
          Close
        </Button>
      </ModalFooter>
    </Modal>
  );
}

/**
 * Return the navbar including all buttons.
 * @param {React.PropsWithChildren<{}>} props
 * @returns {React.FunctionComponentElement}
 */
function TopNavbar({ children = null }) {
  const [ jsonReport ] = useAppState('app.reports.batch.jsonReport', false);
  const jsonReportStatus = jsonReport && jsonReport.status;
  const toolbarStyle = useMemo(
    () => getToolbarStyle(jsonReportStatus),
    [ jsonReportStatus ]
  );
  return useMemo(() => (
    <Navbar light expand='md' className={css(navStyles.toolbar)}>
      <div className={css(navStyles.filterBox)}>
        <FilterBox /*handleNavFilter={this.props.handleNavFilter}*/ />
      </div>
      <Collapse /*isOpen={this.state.isOpen}*/ navbar className={toolbarStyle}>
        <Nav navbar className='ml-auto'>
          {children}
          <InfoButton />
          <FilterButton toolbarStyle={toolbarStyle} />
          <PrintButton />
          <TagsButton />
          <HelpButton />
          <DocumentationButton />
        </Nav>
      </Collapse>
    </Navbar>
  ), [ toolbarStyle, children ]);
}

/**
 * Top toolbar
 * @param {React.PropsWithChildren<{}>} props
 * @returns {React.FunctionComponentElement}
 */
export default function Toolbar({ children = null }) {
  return (
    <div>
      <TopNavbar>
        {children}
      </TopNavbar>
      <HelpModal />
      <InfoModal />
    </div>
  );
}
