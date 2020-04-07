import React from 'react';
import { css } from 'aphrodite';
import Navbar from 'reactstrap/lib/Navbar';
import Nav from 'reactstrap/lib/Nav';
import Collapse from 'reactstrap/lib/Collapse';

import navStyles from '../../../Toolbar/navStyles';
import { STATUS_CATEGORY } from '../../../Common/defaults';
import useReportState from '../hooks/useReportState';
import FilterBox from '../../../Toolbar/FilterBox';
import InfoButton from './InfoButton';
import FilterButton from './FilterButton';
import PrintButton from './PrintButton';
import TagsButton from './TagsButton';
import HelpButton from './HelpButton';
import DocumentationButton from './DocumentationButton';

/**
 * Get the current toolbar style based on the testplan status.
 * @param {StatusType} [status]
 * @returns {ReturnType<typeof css>}
 */
export const getToolbarStyle = (status) => css(
  navStyles.toolbar,
  {
    passed: navStyles.toolbarPassed,
    failed: navStyles.toolbarFailed,
    error: navStyles.toolbarFailed,
    unstable: navStyles.toolbarUnstable,
  }[STATUS_CATEGORY[status]] || navStyles.toolbarUnknown
);

/**
 * Return the navbar including all buttons.
 * @param {React.PropsWithChildren<{}>} props
 * @returns {React.FunctionComponentElement}
 */
export default function TopNavbar({ children = null }) {
  const [ jsonReport ] = useReportState('app.reports.batch.jsonReport', false);
  const jsonReportStatus = jsonReport && jsonReport.status;
  const toolbarStyle = React.useMemo(() => (
    getToolbarStyle(jsonReportStatus)
  ), [ jsonReportStatus ]);
  return React.useMemo(() => (
    <Navbar light expand='md' className={css(navStyles.toolbar)}>
      <div className={css(navStyles.filterBox)}>
        <FilterBox/>
      </div>
      <Collapse navbar className={toolbarStyle}>
        <Nav navbar className='ml-auto'>
          {children}
          <InfoButton/>
          <FilterButton toolbarStyle={toolbarStyle}/>
          <PrintButton/>
          <TagsButton/>
          <HelpButton/>
          <DocumentationButton/>
        </Nav>
      </Collapse>
    </Navbar>
  ), [ toolbarStyle, children ]);
}
