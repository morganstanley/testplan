import React from 'react';
import { Route } from 'react-router-dom';

import useReportState from '../hooks/useReportState';
import EmptyListGroupItem from './EmptyListGroupItem';
import NavBreadcrumbContainer from './NavBreadcrumbContainer';
import NavBreadcrumbWithNextRoute from './NavBreadcrumbWithNextRoute';
import NavSidebarWithNextRoute from './NavSidebarWithNextRoute';
import AutoSelectRedirect from './AutoSelectRedirect';

export default function NavPanes() {
  const [ [ jsonReport, fetchError, isFetching ] ] = useReportState([
    'jsonReport', 'fetchError', 'isFetching',
  ].map(e => `app.reports.batch.${e}`), false);
  return (isFetching || fetchError || !jsonReport)
    ? <EmptyListGroupItem/>
    : (
      <>
        {
          /**
           * Here each path component adds a new breadcrumb to the top nav,
           * and it sets up the next route that will receive the next path
           * component when the user navigates further
           */
        }
        <NavBreadcrumbContainer>
          <Route path='/:id' render={() => (
            <NavBreadcrumbWithNextRoute entries={[ jsonReport ]}/>
          )}/>
        </NavBreadcrumbContainer>
        {
          /**
           * Here each path component completely replaces the nav sidebar.
           * This contains the links that will determine the next set of routes.
           */
        }
        <Route path='/:id' render={() =>
          <NavSidebarWithNextRoute entries={[ jsonReport ]}/>
        }/>
        <Route exact path='/' component={() =>
          <AutoSelectRedirect basePath='/' entry={jsonReport}/>
        }/>
      </>
    );
}
