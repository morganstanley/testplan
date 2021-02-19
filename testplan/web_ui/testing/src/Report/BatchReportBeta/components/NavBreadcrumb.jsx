import React from 'react';
import { NavLink, withRouter } from 'react-router-dom';
import _ from 'lodash';
import { css } from 'aphrodite';
import { connect } from 'react-redux';
import { setSelectedEntry } from '../state/uiActions';
import { mkGetUISelectedEntry } from '../state/uiSelectors';
import {
  CommonStyles,
  navBreadcrumbStyles,
  UNDECORATED_LINK_STYLE,
  ACTIVE_LINK_CLASSES,
} from '../styles';
import NavEntry from '../../../Nav/NavEntry';
import { joinURLComponent } from '../../../Common/utils';

const BREADCRUMB_LINK_CLASSES = css(
  navBreadcrumbStyles.breadcrumbEntry,
  CommonStyles.unselectable,
);

const connector = connect(
  () => {
    const getSelectedEntry = mkGetUISelectedEntry();
    return function mapStateToProps(state) {
      return {
        selectedEntry: getSelectedEntry(state),
      };
    };
  },
  function mapDispatchToProps(dispatch) {
    return {
      boundSetSelectedEntry: entry => dispatch(setSelectedEntry(entry)),
    };
  },
  function mergeProps(stateProps, dispatchProps, ownProps) {
    const { selectedEntry } = stateProps;
    const { boundSetSelectedEntry } = dispatchProps;
    const {
      location: currentLocation,
      match: { url: matchedUrl = '' },
      entry,
    } = ownProps;
    const {
      name: entryName = '',
      uid: entryUid = '',
      category: entryCategory = '',
      status: entryStatus = '',
      counter: {
        passed: nPass = 0,
        failed: nFail = 0,
        error: nError = 0,
      },
    } = entry;
    return {
      entryName,
      entryUid,
      entryCategory,
      entryStatus,
      nPass,
      nFailOrError: nFail + nError,
      to: { ...currentLocation, pathname: joinURLComponent(matchedUrl, '') },
      onClick: () => {
        if(selectedEntry !== entry && _.isObject(entry)) {
          boundSetSelectedEntry(entry);
        }
      },
    };
  }
);

const NavBreadcrumb = ({
  onClick, entryName, entryUid, entryCategory, entryStatus, nPass,
  nFailOrError, to,
}) => (
  <NavLink data-uid={entryUid}
           className={BREADCRUMB_LINK_CLASSES}
           activeClassName={ACTIVE_LINK_CLASSES}
           style={UNDECORATED_LINK_STYLE}
           to={to}
           onClick={onClick}
  >
    <NavEntry type={entryCategory}
              status={entryStatus}
              name={entryName}
              caseCountPassed={nPass}
              caseCountFailed={nFailOrError}
    />
  </NavLink>
);

export default withRouter(connector(NavBreadcrumb));
