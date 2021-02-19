import React from 'react';
import { connect } from 'react-redux';
import { css } from 'aphrodite';
import { Route } from 'react-router';
import { navBreadcrumbStyles } from '../styles';
import {
  mkGetReportIsFetching,
  mkGetReportLastFetchError,
  mkGetReportDocument,
} from '../state/reportSelectors';
import EmptyListGroupItem from './EmptyListGroupItem';
import NavBreadcrumbWithNextRoute from './NavBreadcrumbWithNextRoute';
import NavSidebarWithNextRoute from './NavSidebarWithNextRoute';
import AutoSelectRedirect from './AutoSelectRedirect';

const NAV_BREADCRUMB_CONTAINER_CLASSES = css(
  navBreadcrumbStyles.navBreadcrumbs,
  navBreadcrumbStyles.breadcrumbContainer
);

const connector = connect(
  () => {
    const getReportIsFetching = mkGetReportIsFetching();
    const getReportLastFetchError = mkGetReportLastFetchError();
    const getReportDocument = mkGetReportDocument();
    return function mapStateToProps(state) {
      return {
        document: getReportDocument(state),
        fetchError: getReportLastFetchError(state),
        isFetching: getReportIsFetching(state),
      };
    };
  },
);

const NavPanes = ({ document, fetchError, isFetching }) => {
  const entries = React.useMemo(() => [ document ], [ document ]);
  return (isFetching || fetchError || !document) ? <EmptyListGroupItem/> : (
    <>
      {
        /**
         * Here each path component adds a new breadcrumb to the top nav,
         * and it sets up the next route that will receive the next path
         * component when the user navigates further
         */
      }
      <ul className={NAV_BREADCRUMB_CONTAINER_CLASSES}>
        <Route path='/:id' render={({ match }) => (
          <NavBreadcrumbWithNextRoute entries={entries} match={match} />
        )}/>
      </ul>
      {
        /**
         * Here each path component completely replaces the nav sidebar.
         * This contains the links that will determine the next set of routes.
         */
      }
      <Route path='/:id' render={({ match }) => (
        <NavSidebarWithNextRoute entries={entries} match={match} />
      )}/>
      <Route exact path='/' component={props => (
        <AutoSelectRedirect entry={document} {...props} />
      )}/>
    </>
  );
};

export default connector(NavPanes);
