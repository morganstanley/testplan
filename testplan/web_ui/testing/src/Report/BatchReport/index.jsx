import React, { useRef, useEffect, useCallback, useMemo } from 'react';
import _at from 'lodash/at';
import _isEqual from 'lodash/isEqual';
import { css } from 'aphrodite';
import axios from 'axios';
import { ListGroupItem, ListGroup } from 'reactstrap';
import {
  Redirect, Route, NavLink, useRouteMatch, useParams, useLocation, Switch
} from 'react-router-dom';
import PropTypes from 'prop-types';

import { PropagateIndices } from '../reportUtils';
import CenterPane from './CenterPane';
import Toolbar from './Toolbar';
import NavEntry from '../../Nav/NavEntry';
import TagList from '../../Nav/TagList';
import Column from '../../Nav/Column';
import { queryStringToMap } from '../../Common/utils';

import {
  CommonStyles, navBreadcrumbStyles, navUtilsStyles, navListStyles,
  COLUMN_WIDTH, batchReportStyles,
} from './style';
import uriComponentCodec from './uriComponentCodec';
import { AppStateProvider, useAppState } from './state';
import UIRouter from './UIRouter';

const BOTTOMMOST_ENTRY_CATEGORY = 'testcase';

const safeGetNumPassedFailedErrored = (counter, coalesceVal = null) => counter ?
  [
    counter.passed || coalesceVal,
    counter.failed || coalesceVal,
    counter.error || coalesceVal,
  ] : [ coalesceVal, coalesceVal, coalesceVal ];

function getAxiosConfig() {
  const axiosConf = { headers: axios.defaults.headers.common };
  try {
    if(process.env.NODE_ENV === 'development') {
      let dbOverride = null;
      try {
        dbOverride = process.env.REACT_APP_DB_HOST;
      } catch(err) {
        console.error(err);
      }
      if(dbOverride) {
        axiosConf.baseURL = dbOverride;
        const dbOverrideOrigin = new URL(dbOverride).origin;
        if(window.location.origin !== dbOverrideOrigin) {
          // CORS headers: developer.mozilla.org/en-US/docs/Web/HTTP/CORS
          axiosConf.headers['Access-Control-Allow-Origin'] = dbOverrideOrigin;
        }
      }
    }
  } catch(err) {
    console.error(err);
    return {};
  }
  return axiosConf;
}

function getUidOverride() {
  try {
    return process.env.REACT_APP_REPORT_UID_OVERRIDE;
  } catch(err) {
    return null;
  }
}

const isFilteredOut = (filter, [ numPassed, numFailed, numErrored ]) =>
  (filter === 'pass' && numPassed === 0) ||
  (filter === 'fail' && (numFailed + numErrored) === 0);

function useFetchJsonReport(reportUid, isDev = false) {

  const [, [ setJsonReport, setLoading, setFetching, setFetchError, ]] =
    useAppState(false, [
      'setAppBatchReportJsonReport',
      'setAppBatchReportIsLoading',
      'setAppBatchReportIsFetching',
      'setAppBatchReportFetchError',
    ]);

  const setJsonReportCb = useCallback(setJsonReport, []),
    setLoadingCb = useCallback(setLoading, []),
    setFetchingCb = useCallback(setFetching, []),
    setFetchErrorCb = useCallback(setFetchError, []);

  useEffect(() => {
    console.debug('>>> Starting fetch...');
    const fetchCanceller = axios.CancelToken.source();
    // importing like this means webpack *may* exclude fakeReport.js from the
    // production bundle
    const fetchFakeAssertions = () => import('../../Common/fakeReport').then(
      fakeReport => fakeReport.fakeReportAssertions
    );
    const fetchReport = () => axios.get(
      `/api/v1/reports/${reportUid}`,
      { ...getAxiosConfig(), cancelToken: fetchCanceller.token }
    );
    (async () => {
      let isCancelled = false;
      setLoadingCb(true);
      try {
        setFetchingCb(true);
        const report = await (
          isDev && !getUidOverride() ? fetchFakeAssertions() : fetchReport()
        );
        setFetchingCb(false);
        setJsonReportCb(PropagateIndices(report.data));
      } catch(err) {
        if(!axios.isCancel(err)) { // can't set state after cleanup func runs
          setFetchErrorCb(err);
        } else {
          isCancelled = true;
          console.error(err);
        }
      }
      if(!isCancelled) {
        setLoadingCb(false);
        console.debug('>>> Ending fetch...');
      }
    })();
    return () => {
      fetchCanceller.cancel('Fetch cancelled due to component cleanup');
    };
  }, [
    reportUid, isDev,
    setLoadingCb, setFetchingCb, setJsonReportCb, setFetchErrorCb,
  ]);
}

function useTargetEntry(entries) {
  // Assume:
  // - The route that was matched === "/aaa/bbb/ccc/:id"
  // - The URL that matched       === "/aaa/bbb/ccc/12345"
  // Then the value of the following variables are:
  // *   url = "/aaa/bbb/ccc/12345"
  // *  path = "/aaa/bbb/ccc/:id"
  // *    id = "12345"
  const { id: encodedID } = useParams();
  const [ aliases, setUriHashPathComponentAlias ] = useAppState(
    'uri.hash.aliases',
    'setUriHashPathComponentAlias'
  );

  // gotta run hooks before we do this check since they must run unconditionally
  if(!Array.isArray(entries)) return null;
  if(
    !!entries && typeof entries === 'object' &&
    entries.category === BOTTOMMOST_ENTRY_CATEGORY
  ) return entries;

  // ths incoming `encodedID` may be URL-encoded and so it won't match
  // `entry.name` in the `entries` array, so we grab whatever `id` is actually
  // an alias for, and use that to find our target `entry` object.
  let decodedID = aliases.get(encodedID);

  // on refresh on an aliased path, the `componentAliases` will be empty so we
  // need to fill it with the aliased component
  if(!decodedID) {
    decodedID = uriComponentCodec.decode(encodedID);
    setUriHashPathComponentAlias(decodedID, encodedID);
  }
  return entries.find(e => decodedID === e.name);
}

const EmptyListGroupItem = () => (
  <ListGroupItem className={css(navUtilsStyles.navButton)}>
    No entries to display...
  </ListGroupItem>
);

const NavBreadcrumbContainer = ({ children }) => (
  <div className={css(navBreadcrumbStyles.navBreadcrumbs)}>
    <ul className={css(navBreadcrumbStyles.breadcrumbContainer)}>
      {children}
    </ul>
  </div>
);

const StyledNavLink = ({
  style = { textDecoration: 'none', color: 'currentColor' },
  isActive = () => false,  // this just makes it look better
  pathname,
  dataUid,
  ...props
}) => {
  const [ selectedTestCase ] =
    useAppState('app.reports.batch.selectedTestCase');
  // ensure links always include the current query params
  const { search } = useLocation();
  // remove repeating slashes
  const normPathname = pathname.replace(/\/{2,}/g, '/');
  const to = { search, pathname: normPathname };
  return /*useMemo(() =>*/ (
    <NavLink style={style}
             data-uid={dataUid}
             isActive={(match, location) =>
               !!selectedTestCase &&
               !!(selectedTestCase.uid) &&
               selectedTestCase.uid === dataUid
             }
             activeClassName={css(navUtilsStyles.navButtonInteract)}
             to={to}
             {...props}
    />
    // eslint-disable-next-line react-hooks/exhaustive-deps
  )/*, [ search, normPathname, props, style, isActive, selectedTestCase ])*/;
};
StyledNavLink.propTypes = {
  pathname: PropTypes.string.isRequired,
  dataUid: PropTypes.string.isRequired,
  style: PropTypes.object,
  isActive: PropTypes.func
};

const NavBreadcrumb = ({ entry }) => {
  const { name, status, category, counter, uid } = entry;
  const [, setSelectedTestCase ] = useAppState(
    false, 'setAppBatchReportSelectedTestCase'
  );
  // this is the matched Route, not necessarily the current URL
  const { url: matchedPath } = useRouteMatch();
  const [ numPassed, numFailed ] = safeGetNumPassedFailedErrored(counter, 0);
  return (
    <StyledNavLink pathname={matchedPath}
                   dataUid={uid}
                   className={css(
                     navBreadcrumbStyles.breadcrumbEntry,
                     CommonStyles.unselectable,
                   )}
                   onClick={evt => {
                     setSelectedTestCase(null);
                   }}
    >
      <NavEntry name={name}
                status={status}
                type={category}
                caseCountPassed={numPassed}
                caseCountFailed={numFailed}
      />
    </StyledNavLink>
  );
};

const StyledListGroupItemLink = props => (
  <ListGroupItem {...props}
                 tag={StyledNavLink}
                 className={css(
                   navUtilsStyles.navButton,
                   navUtilsStyles.navButtonInteract,
                 )}
  />
);

function BoundStyledListGroupItemLink({ entry, idx, nPass, nFail }) {

  const
    { url } = useRouteMatch(),
    { name, status, category, tags, uid } = entry,
    [ isShowTags, [ setUriHashPathComponentAlias, setSelectedTestCase ] ] =
      useAppState(
        'app.reports.batch.isShowTags',
        [ 'setUriHashPathComponentAlias', 'setAppBatchReportSelectedTestCase' ]
      );
  // setSelectedTestCase(null);
  const
    isBottommost = category === BOTTOMMOST_ENTRY_CATEGORY,
    encodedName = uriComponentCodec.encode(name),
    nextPathname = /**/isBottommost ? url :/**/ `${url}/${encodedName}`,
    onClickOverride = !isBottommost ? {
      onClick(evt) { setSelectedTestCase(null); }
    } : {
      onClick(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        setSelectedTestCase(entry);
      }
    };
  setUriHashPathComponentAlias(encodedName, name);

  return (
    <StyledListGroupItemLink key={uid}
                             uid={uid}
                             tabIndex={`${idx + 1}`}
                             pathname={nextPathname}
                             {...onClickOverride}
    >
      {
        isShowTags && tags
          ? <TagList entryName={name} tags={tags}/>
          : null
      }
      <NavEntry caseCountPassed={nPass}
                caseCountFailed={nFail}
                type={category}
                status={status}
                name={name}
      />
    </StyledListGroupItemLink>
  );
}

const NavSidebar = ({ entries }) => {
  const [ filter ] = useAppState('app.reports.batch.filter', false);
  const items = entries.map((entry, idx) => {
    const [ nPass, nFail ] = safeGetNumPassedFailedErrored(entry.counter, 0);
    return isFilteredOut(filter, [ nPass, nFail ]) ? null : (
      <BoundStyledListGroupItemLink entry={entry}
                                    idx={idx}
                                    key={`${idx}`}
                                    nPass={nPass}
                                    nFail={nFail}
      />
    );
  }).filter(e => !!e);
  return (
    <Column width={COLUMN_WIDTH}>
      <ListGroup className={css(navListStyles.buttonList)}>
        {items.length ? items : <EmptyListGroupItem/>}
      </ListGroup>
    </Column>
  );
};

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

/**
 * @param {any | any[] | null} entries
 * @param {React.Component | null} PreviousNavSidebar
 * @param {string | null} previousUrl
 * @returns {React.FunctionComponentElement}
 */
const NavSidebarWithNextRoute = ({
  /*match,*/ /*location,*/
  entries, PreviousNavSidebar = null,
  previousPath = null, isBottom = false, bottommostPath = null,
}) => {
  const match = useRouteMatch();
  // const location = useLocation();
  const tgtEntry = useTargetEntry(entries);

  // const [, setSelectedTestCase ] = useAppState(
  //   false,
  //   'setAppBatchReportSelectedTestCase'
  // );

  if(!tgtEntry) return null;
  const isBottommost = tgtEntry.category === BOTTOMMOST_ENTRY_CATEGORY;
  // let nextRoutePath = `${url}/:id`;
  // if(isBottommost) {
  // if(tgtEntry.category === BOTTOMMOST_ENTRY_CATEGORY) {
  //   [ nextEntries, nextSuperEntries ] = [ entries, superEntries ];
  //   nextRoutePath = url;
  //   setSelectedTestCase(isBottommost ? tgtEntry : null);
  //   const toLocation = {
  //     ...location,
  //     pathname: previousPath || location.pathname
  //   };
  //   return <Redirect to={toLocation} push={false} />;
    // return PreviousNavSidebar === null ? null : <PreviousNavSidebar/>;
  // }

  const ThisNavSidebar = props => (
  //   <Route exact path={match.url} render={routeProps =>
      <NavSidebar entries={tgtEntry.entries} {...props} />
  //   }/>
  );

  if(isBottom) {
    let x = 1;
  }

  if(isBottommost) {
    let x = 1;
  }

  if(bottommostPath === null && isBottommost) {
    bottommostPath = previousPath;
  }

  const routePath =
    typeof bottommostPath === 'string' ?
      bottommostPath :
      match.url;

  return (
    <>
      <Route exact path={routePath} render={props => {
        // <NavSidebar entries={tgtEntry.entries} {...routeProps} />
        // <ThisNavSidebar {...routeProps}/>
        // if(isBottommost) {
          // setSelectedTestCase(tgtEntry);
          // return <PreviousNavSidebar/>;
        // }
        // return <NavSidebar entries={tgtEntry.entries} {...props} />;
        return <ThisNavSidebar/>;
      }}/>
      <Route path={`${routePath}/:id`}>
        {(() => {
          // setSelectedTestCase(null);
          return isBottommost ?
            <Redirect to={bottommostPath} push={false} /> : (
              <NavSidebarWithNextRoute entries={tgtEntry.entries}
                                       PreviousNavSidebar={() =>
                                         <ThisNavSidebar/>
                                       }
                                       previousPath={routePath}
                                       isBottom={isBottommost}
                                       bottommostPath={bottommostPath}
              />
            );
        })()}
      </Route>
    </>
  );

  // if(isBottommost) {
  //   return (
  //     <>
  //       {/*<NavSidebar entries={tgtEntry.entries} />*/}
  //       <PreviousNavSidebar/>
  //       <Route path={`${match.url}/:id`}>
  //         <NavSidebarWithNextRoute entries={tgtEntry.entries}
  //                                  PreviousNavSidebar={PreviousNavSidebar}
  //                                  previousPath={location.pathname}
  //         />
  //       </Route>
  //     </>
  //   );
  // } else {
  //   return (
  //     <>
  //       <Route exact path={match.url} render={routeProps =>
  //         // <NavSidebar entries={tgtEntry.entries} {...routeProps} />
  //         <ThisNavSidebar {...routeProps}/>
  //       }/>
  //       <Route path={`${match.url}/:id`}>
  //         <NavSidebarWithNextRoute entries={tgtEntry.entries}
  //                                  PreviousNavSidebar={ThisNavSidebar}
  //                                  previousPath={location.pathname}
  //         />
  //       </Route>
  //     </>
  // );
  // }

  // return (
  //   <>
  //     <ThisNavSidebar/>
  //
  //     {/*<Route path={`${match.url}/:id`} render={routeProps =>*/}
  //     {/*  <NavSidebarWithNextRoute entries={tgtEntry.entries}*/}
  //     {/*                           PreviousNavSidebar={ThisNavSidebar}*/}
  //     {/*                           previousPath={location.pathname}*/}
  //     {/*                           {...routeProps}*/}
  //     {/*  />*/}
  //     {/*}/>*/}
  //
  //     {/*<Route path={`${match.url}/:id`} component={routeProps =>*/}
  //     {/*  <NavSidebarWithNextRoute entries={tgtEntry.entries}*/}
  //     {/*                           PreviousNavSidebar={ThisNavSidebar}*/}
  //     {/*                           previousPath={location.pathname}*/}
  //     {/*                           {...routeProps}*/}
  //     {/*  />*/}
  //     {/*}/>*/}
  //
  //     <Route path={`${match.url}/:id`}>
  //       <NavSidebarWithNextRoute entries={tgtEntry.entries}
  //                                PreviousNavSidebar={ThisNavSidebar}
  //                                previousPath={location.pathname}
  //       />
  //     </Route>
  //
  //   </>
  // );
};

/**
 * Jump ahead through objects with only one entry if we don't have
 * `doAutoSelect === false`
 * @param {React.PropsWithoutRef<{entry: any, basePath: string}>} props
 * @returns {Redirect}
 */
function AutoSelectRedirect({ entry, basePath }) {
  const [ doAutoSelect ] = useAppState('app.reports.batch.doAutoSelect', false);
  // trim trailing slashes from basePath and join with the first entry's name
  let toPath = `${basePath.replace(/\/+$/, '')}/${entry.name || ''}`;
  if(doAutoSelect) {
    while(entry.category !== 'testcase'
          && Array.isArray(entry.entries)
          && entry.entries.length === 1
          && typeof (entry = entry.entries[0] || {}) === 'object'
          && typeof (entry.name) === 'string'
      ) { toPath = `${toPath}/${entry.name}`; }
  }
  return <Redirect to={toPath} push={false} />;
}

function NavPanes() {
  const [
    [ jsonReport, fetchError, isFetching ],
    // setSelectedTestCase,
  ] = useAppState([
    'jsonReport', 'fetchError', 'isFetching',
  ].map(e => `app.reports.batch.${e}`),
  false  // 'setAppBatchReportSelectedTestCase',
  );

  // setSelectedTestCase(null);
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

    {/*<Route path='/:id'>*/}
    {/* <NavSidebarWithNextRoute entries={[ jsonReport ]} filter={filter} />*/}
    {/*</Route>*/}

        <Route path='/:id' render={props =>
          <NavSidebarWithNextRoute entries={[ jsonReport ]} {...props} />
        }/>

        <Route exact path='/' component={() =>
          <AutoSelectRedirect basePath='/' entry={jsonReport}/>
        }/>
      </>
    );
}

function BatchReportStartup({ browserProps, children = null }) {
  const currLocation = useLocation();
  const [, mapQueryToState ] = useAppState(false, 'mapUriHashQueryToState');
  const isFirstRenderRef = useRef(true);
  const currQueryMap = queryStringToMap(currLocation.search);
  const prevQueryMapRef = useRef(currQueryMap);
  const queryChanged = !_isEqual(currQueryMap, prevQueryMapRef.current);
  if(queryChanged || isFirstRenderRef.current) {
    prevQueryMapRef.current = currQueryMap;
    isFirstRenderRef.current = false;
    mapQueryToState(currQueryMap);
  }
  useFetchJsonReport(browserProps.match.params.uid, !!(
    process.env.NODE_ENV === 'development' && _at(
      Object.fromEntries([
        ...queryStringToMap(browserProps.location.search),
        ...currQueryMap,
      ]),
      ['dev', 'devel', 'development'],
    ).filter(e => !!e).reduce((p, c) => p || c)
  ));
  return children;
}
BatchReportStartup.propTypes = {
  browserProps: PropTypes.shape({
    match: PropTypes.object,
    location: PropTypes.object,
    history: PropTypes.object,
  }).isRequired,
  children: PropTypes.element,
};

export default function BatchReport({ match, location, history }) {
  return (
    <AppStateProvider>
      <UIRouter>
        <BatchReportStartup browserProps={{ match, location, history }} >
          <div className={css(batchReportStyles.batchReport)}>
            <Toolbar/>
            <NavPanes/>
            <CenterPane/>
          </div>
        </BatchReportStartup>
      </UIRouter>
    </AppStateProvider>
  );
}
