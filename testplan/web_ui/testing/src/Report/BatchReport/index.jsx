import React, { useEffect, useState } from 'react';
import { StyleSheet, css } from 'aphrodite';
import axios from 'axios';
import { ListGroupItem, ListGroup } from 'reactstrap';
import {
  HashRouter, Redirect, Route, NavLink, useRouteMatch, useParams, generatePath,
  matchPath
} from 'react-router-dom';

import { PropagateIndices } from '../reportUtils';
import AssertionPane from '../../AssertionPane/AssertionPane';
import Toolbar from '../../Toolbar/Toolbar';
import NavEntry from '../../Nav/NavEntry';
import TagList from '../../Nav/TagList';
import Column from '../../Nav/Column';
import Message from '../../Common/Message';
import { ParsedQueryParams, tryCatch } from '../../Common/utils';

import {
  CommonStyles, navBreadcrumbStyles, navUtilsStyles, navListStyles, COLUMN_WIDTH
} from './style';
import uriComponentCodec from './uriComponentCodec';
import { AppStateProvider, useAppState } from './state';

const batchReportStyles = StyleSheet.create({
  batchReport: {
    /** overflow will hide dropdown div */
    // overflow: 'hidden'
  }
});

const safeGetNumPassedFailedErrored = (counter, coalesceVal = null) => counter ?
  [
    counter.passed || coalesceVal,
    counter.failed || coalesceVal,
    counter.error || coalesceVal,
  ] : [ null, null, null ];

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

function encodeRememberURIComponent(rawURIComponent, setAlias, aliasMap) {
  const encodedURIComponent = uriComponentCodec.encode(rawURIComponent);
  if(!aliasMap.has(rawURIComponent)) {
    setAlias(rawURIComponent, encodedURIComponent);
  }
  return encodedURIComponent;
}

function decodeForgetURIComponent(encodedURIComponent, deleteAlias, aliasMap) {
  const rawURIComponent = uriComponentCodec.decode(encodedURIComponent);
  if(aliasMap.has(rawURIComponent)) {
    deleteAlias(rawURIComponent, encodedURIComponent);
  }
  return rawURIComponent;
}

function segregateByEncoded({ url, path, id }) {

  let idIsProbablyEncoded = false;
  try {
    idIsProbablyEncoded = id.length >= decodeURIComponent(id).length;
  } catch(e) {}

  const [ idEncoded, idUnencoded ] = (
    idIsProbablyEncoded
      ? [ id, decodeURIComponent(id) ]
      : [ encodeURIComponent(id), id ]
  );

  let urlIsProbablyEncoded = false;
  try {
    urlIsProbablyEncoded = url.length >= decodeURI(url).length;
  } catch(e) {}

  const [ urlEncoded, urlUnencoded] = (
    urlIsProbablyEncoded  // assuming if url is encoded then path is enccoded
      ? [ generatePath(path, { idUnencoded }), decodeURI(url) ]
      : [ decodeURI(url), generatePath(path, { idUnencoded }) ]
  );

  return {
    encoded: {
      url: urlEncoded,
      id: idEncoded,
    },
    unencoded: {
      url: urlUnencoded,
      id: idUnencoded,
    }
  };
}

const NavBreadcrumb = ({ entry }) => {
  const { name, status, category, counter } = entry;
  const { url } = useRouteMatch();
  const lkCss = css(
    navBreadcrumbStyles.breadcrumbEntry,
    CommonStyles.unselectable,
  );
  const [ numPassed, numFailed ] = safeGetNumPassedFailedErrored(counter, 0);
  const lkStyle = { textDecoration: 'none', color: 'currentColor' };
  return (
    <NavLink to={url} className={lkCss} isActive={() => false} style={lkStyle}>
      <NavEntry name={name}
                status={status}
                type={category}
                caseCountPassed={numPassed}
                caseCountFailed={numFailed}
      />
    </NavLink>
  );
};

const NavSidebar = ({ entries, filter, displayTags }) => {

  let { url } = useRouteMatch();
  const [ appState, appAction ] = useAppState();

  const aliasMap = appState.app.reports.batch.uri.hash.componentAliases;
  const setAlias = appAction.setUriHashComponentAlias;

  const StyledListGroupItemLink = ({ children, to, linkIdx }) => {
    const StyledLink = props => (
      <NavLink style={{ textDecoration: 'none', color: 'currentColor' }}
               isActive={() => false}
               to={to}
               {...props}
      />
    );
    return (
      <ListGroupItem tabIndex={`${linkIdx + 1}`}
                     tag={StyledLink}
                     className={css(
                       navUtilsStyles.navButton,
                       navUtilsStyles.navButtonInteract,
                     )}
      >
        {children}
      </ListGroupItem>
    );
  };

  const isFilteredOut = ([ numPassed, numFailed, numErrored ]) =>
    (filter === 'pass' && numPassed === 0) ||
    (filter === 'fail' && (numFailed + numErrored) === 0);

  function BoundStyledListGroupItemLink({ entry, idx, nPass, nFail }) {
    const { name, status, category, tags, uid } = entry;
    const encodedName = encodeRememberURIComponent(name, setAlias, aliasMap);
    const toURL = `${url}/${encodedName}`;
    return (
      <StyledListGroupItemLink key={uid} linkIdx={idx} to={toURL}>
        {displayTags && tags ? <TagList entryName={name} tags={tags}/> : null}
        <NavEntry caseCountPassed={nPass}
                  caseCountFailed={nFail}
                  type={category}
                  status={status}
                  name={name}
        />
      </StyledListGroupItemLink>
    );
  }

  const items = entries.map((entry, idx) => {
    const [ nPass, nFail ] = safeGetNumPassedFailedErrored(entry.counter, 0);
    return isFilteredOut([ nPass, nFail ]) ? null : (
      <BoundStyledListGroupItemLink entry={entry}
                                    idx={idx}
                                    nPass={nPass}
                                    nFail={nFail}
      />
    );
  }).filter(e => !!e);

  return (
    <Column width={COLUMN_WIDTH}>
      <ListGroup className={css(navListStyles.buttonList)}>
        {
          items.length
            ? items
            : <EmptyListGroupItem/>
        }
      </ListGroup>
    </Column>
  );
};

const NavBreadcrumbWithNextRoute = ({ entries }) => {
  // Assume:
  // - The route that was matched === "/aaa/bbb/ccc/:id"
  // - The URL that matched       === "/aaa/bbb/ccc/12345"
  // Then the value of the following variables are:
  // *   url = "/aaa/bbb/ccc/12345"
  // *  path = "/aaa/bbb/ccc/:id"
  // *    id = "12345"
  const { url, ...matchProps } = useRouteMatch();
  const { id } = useParams();

  // this is needed so any forward slashes in `id` are URL encoded
  // const encodedURL = generatePath(path, { id });

  const tgtEntry =
    entries && Array.isArray(entries) && entries.find(e => id === e.name);
  if(!tgtEntry) return null;
  return !tgtEntry ? null : (
    <>
      <NavBreadcrumb entry={tgtEntry}/>
      <Route path={`${url}/:id`} render={() =>
        <NavBreadcrumbWithNextRoute entries={tgtEntry.entries || []}/>
      }/>
    </>
  );
};

const NavSidebarWithNextRoute = ({ entries, filter, displayTags }) => {
  const { url, path } = useRouteMatch();
  const { id: encodedID } = useParams();

  const decodedID = uriComponentCodec.decode(encodedID);
  const tgtEntry = Array.isArray(entries) &&
                   entries.find(e => decodedID === e.name);
  if(!tgtEntry) return null;

  return !tgtEntry ? null : (
    <>
      <Route exact path={url} render={() =>
        <NavSidebar entries={tgtEntry.entries}
                    filter={filter}
                    displayTags={displayTags}
        />
      }/>
      <Route path={`${url}/:id`}>
        <NavSidebarWithNextRoute entries={tgtEntry.entries}
                                 displayTags={displayTags}
                                 filter={filter}
        />
      </Route>
    </>
  );
};

const NavPanes = ({
  isFetching, isLoading, isError, report, filter, displayTags
}) => (
  (isFetching || isLoading || isError || !report)
    ? <EmptyListGroupItem/>
    : (
      <>
        {
          /** Here each path component adds a new breadcrumb to the top nav,
           * and it sets up the next route that will receive the next path
           * component when the user navigates further
           */
        }
        <NavBreadcrumbContainer>
          <Route path='/:id' render={() => (
            <NavBreadcrumbWithNextRoute entries={[ report ]}/>
          )}/>
        </NavBreadcrumbContainer>
        {
          /** Here each path component completely replaces the nav sidebar.
           * This contains the links that will determine the next set of routes.
           */
        }
        <Route path='/:id'>
          <NavSidebarWithNextRoute entries={[ report ]}
                                   displayTags={displayTags}
                                   filter={filter}
          />
        </Route>
        <Route exact path='/' component={() => (
          <Redirect to={`/${report.name}`}/>
        )}/>
      </>
    )
);

const CenterPane = ({
  isFetching, isLoading, error, assertions, logs, filter, reportUid,
  testcaseUid, description,
}) => {
  if(isFetching) {
    return (
      <Message left={COLUMN_WIDTH}
               message='Fetching Testplan report...'
      />
    );
  }
  if(error) {
    return (
      <Message left={COLUMN_WIDTH}
               message={() =>
                 'Error fetching Testplan report. '
                 + (error instanceof Error ? ` (${error.message})` : '')
               }
      />
    );
  }
  if(isLoading) {
    return (
      <Message left={COLUMN_WIDTH}
               message='Waiting to fetch Testplan report...'
      />
    );
  }
  if(reportUid && (assertions || (Array.isArray(logs) && logs.length))) {
    return (
      <AssertionPane assertions={assertions}
                     logs={logs}
                     descriptionEntries={description}
                     left={COLUMN_WIDTH + 1.5}
                     testcaseUid={testcaseUid}
                     filter={filter}
                     reportUid={reportUid}
      />
    );
  }
  return (
    <Message left={COLUMN_WIDTH} message='Please select an entry.'/>
  );
};

/**
 * If the current report entry has only one child entry and that entry is
 * not a testcase, we automatically expand it.
 */
const autoSelect = ({ reportUid, reportEntries}) => [ reportUid ].concat(
  reportEntries.length === 1 && reportEntries[0].category !== 'testcase'
    ? autoSelect(reportEntries[0])
    : []
);

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

export default function TopLevel(browserRouterProps) {

  const urlQuery = new ParsedQueryParams(browserRouterProps.location.search);

  // <editor-fold desc="State setters & variables">
  const [ isDev, setDev ] = useState(
    tryCatch(() => process.env.NODE_ENV === 'development') &&
    urlQuery.firstOf(['dev', 'devel', 'development'], false)
  );
  const [ displayEmpty, setDisplayEmpty ] = useState(
    !!urlQuery.get('displayEmpty', true)
  );
  const [ filter, setFilter ] = useState(
    urlQuery.get('filter', 'all')
  );  // or 'pass' or 'fail'
  const [ navFilter, setNavFilter ] = useState(
    urlQuery.get('navFilter', null)
  );
  const [ displayTags, setDisplayTags ] = useState(
    urlQuery.get('displayTags', false)
  );
  const [ loading, setLoading ] = useState(true);
  const [ fetching, setFetching ] = useState(false);
  const [ report, setReport ] = useState({});
  const [ fetchError, setFetchError ] = useState(null);
  const [ centerPane, setCenterPane ] = useState(null);
  const [ selectedUIDs, setselectedUIDs ] = useState([]);
  //</editor-fold>

  const reportUid = browserRouterProps.match.params.uid;
  useEffect(() => {
    console.debug('>>> Starting fetch...');
    (async () => {
      setLoading(true);
      try {
        const axiosConfig = getAxiosConfig();
        setFetching(true);
        const report = (
          isDev && !getUidOverride()
            // importing like this means webpack *may* exclude fakeReport.js
            // from the production bundle
            ? (await import('../../Common/fakeReport')).fakeReportAssertions
            : await axios.get(
              `/api/v1/reports/${reportUid}`,
              axiosConfig
            )
        );
        setFetching(false);
        setReport(PropagateIndices(report.data));
      } catch(err) {
        setFetchError(err);
      }
      setLoading(false);
      console.debug('>>> Ending fetch...');
    })();
  }, [ reportUid, isDev ]);

  return (
    <HashRouter basename='/'>
      <AppStateProvider>
        <div className={css(batchReportStyles.batchReport)}>
          <Toolbar status={report.status}
                   report={report}
                   handleNavFilter={setNavFilter}
                   updateFilterFunc={setFilter}
                   updateEmptyDisplayFunc={setDisplayEmpty}
                   updateTagsDisplayFunc={setDisplayTags}
          />
          <NavPanes isFetching={fetching}
                    isLoading={loading}
                    isError={!!fetchError}
                    report={report}
                    filter={filter}
                    displayTags={displayTags}
          />
          <CenterPane isFetching={fetching}
                      isLoading={loading}
                      error={fetchError}
          />
        </div>
      </AppStateProvider>
    </HashRouter>
  );
}
