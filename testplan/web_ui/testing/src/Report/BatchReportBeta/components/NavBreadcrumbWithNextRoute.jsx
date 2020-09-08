import React from 'react';
import { Route } from 'react-router';
import _ from 'lodash';
import NavBreadcrumb from './NavBreadcrumb';
import { joinURLComponent } from '../../../Common/utils';

const NavBreadcrumbWithNextRoute = ({ entries, match }) => {
  const routePath = _.isObject(match) ? match.url : null;
  const tgtEntry = React.useMemo(() => {
    if(_.isArray(entries) && _.isObject(match)) {
      const decodedName = decodeURIComponent(match.params.id);
      return entries.find(e => decodedName === e.name);
    } else if(_.isObject(entries)) {
      return entries;
    }
    return null;
  }, [ entries, match ]);
  const  tgtEntryIsObj = _.isObject(tgtEntry);
  const tgtEntryEntries = tgtEntryIsObj ? tgtEntry.entries : null;
  return !(tgtEntryIsObj && _.isString(routePath)) ? null : (
    <>
      <NavBreadcrumb entry={tgtEntry}/>
      <Route path={joinURLComponent(routePath, ':id')}
             render={({ match }) => (
               <NavBreadcrumbWithNextRoute entries={tgtEntryEntries}
                                           match={match}
               />
             )}/>
    </>
  );
};

export default NavBreadcrumbWithNextRoute;
