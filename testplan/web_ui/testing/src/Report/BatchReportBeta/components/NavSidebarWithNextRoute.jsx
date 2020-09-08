import React from 'react';
import { Route } from 'react-router';
import _ from 'lodash';
import { BOTTOMMOST_ENTRY_CATEGORY } from '../../../Common/defaults';
import NavSidebar from './NavSidebar';

const NavSidebarWithNextRoute = ({ entries, passedLast, match }) => {

  const routePath = _.isObject(match) ? match.url : null;
  const abortRender = !_.isObject(match) || passedLast;
  const isLast = (
    _.isObject(entries) && entries.category === BOTTOMMOST_ENTRY_CATEGORY
  );

  const tgtEntries = React.useMemo(() => {
    let tgt = null;
    if(!abortRender && _.isObject(entries)) {
      tgt = entries;
      if(_.isArray(entries) && _.isObject(match)) {
        const decodedName = decodeURIComponent(match.params.id);
        tgt = entries.find(e => decodedName === e.name);
      }
    }
    return tgt !== null ? tgt.entries : null;
  }, [ abortRender, entries, match ]);

  return abortRender ? null : (
    <>
      <Route exact
             path={routePath}
             render={({ location, match }) => (
               <NavSidebar entries={tgtEntries}
                           location={location}
                           match={match}
               />
             )}
      />
      <Route path={`${routePath}/:id`}
             children={({ match }) => (
               <NavSidebarWithNextRoute entries={tgtEntries}
                                        passedLast={passedLast || isLast}
                                        match={match}
               />
             )}
      />
    </>
  );
};

export default NavSidebarWithNextRoute;
