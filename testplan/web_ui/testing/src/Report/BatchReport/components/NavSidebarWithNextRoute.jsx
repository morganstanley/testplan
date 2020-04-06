import React from 'react';
import { Redirect, Route, useRouteMatch } from 'react-router-dom';

import useTargetEntry from '../hooks/useTargetEntry';
import { BOTTOMMOST_ENTRY_CATEGORY } from '../../../Common/defaults';
import NavSidebar from './NavSidebar';

/**
 * @param {any | any[] | null} entries
 * @param {string} [previousPath]
 * @param {string} [bottommostPath]
 * @returns {React.FunctionComponentElement}
 */
const NavSidebarWithNextRoute = ({ entries, previousPath, bottommostPath }) => {
  const { url } = useRouteMatch();
  const tgtEntry = useTargetEntry(entries);
  if(!tgtEntry) return null;
  const isBottommost = tgtEntry.category === BOTTOMMOST_ENTRY_CATEGORY;
  if(typeof bottommostPath === 'undefined' && isBottommost && previousPath) {
    bottommostPath = previousPath;
  }
  const routePath = typeof bottommostPath === 'string' ? bottommostPath : url;
  return (
    <>
      <Route exact path={routePath} render={() =>
        <NavSidebar entries={tgtEntry.entries}/>
      }/>
      <Route path={`${routePath}/:id`}>
        {(() => isBottommost ? <Redirect to={bottommostPath} push={false}/> : (
            <NavSidebarWithNextRoute entries={tgtEntry.entries}
                                     previousPath={routePath}
                                     bottommostPath={bottommostPath}
            />
          )
        )()}
      </Route>
    </>
  );
};

export default NavSidebarWithNextRoute;
