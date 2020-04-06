import React from 'react';
import { Route, useRouteMatch } from 'react-router-dom';

import useTargetEntry from '../hooks/useTargetEntry';
import NavBreadcrumb from './NavBreadcrumb';

const NavBreadcrumbWithNextRoute = ({ entries }) => {
  const { url } = useRouteMatch();
  const tgtEntry = useTargetEntry(entries);
  return !tgtEntry ? null : (
    <>
      <NavBreadcrumb entry={tgtEntry}/>
      <Route path={`${url}/:id`} render={() =>
        <NavBreadcrumbWithNextRoute entries={tgtEntry.entries}/>
      }/>
    </>
  );
};

export default NavBreadcrumbWithNextRoute;
