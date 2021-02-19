import React from 'react';
import { Redirect } from 'react-router';
import { connect } from 'react-redux';
import _ from 'lodash';
import { setSelectedEntry } from '../state/uiActions';
import { BOTTOMMOST_ENTRY_CATEGORY } from '../../../Common/defaults';
import { joinURLComponent } from '../../../Common/utils';

const connector = connect(
  null,
  function mapDispatchToProps(dispatch) {
    return   {
      boundSetSelectedEntry: entry => dispatch(setSelectedEntry(entry)),
    };
  },
  function mergeProps(stateProps, dispatchProps, ownProps) {
    const { boundSetSelectedEntry } = dispatchProps;
    const { location, entry } = ownProps;
    return {
      getRedirectToEntry: () => {
        const to = {
          ...location,
          pathname: joinURLComponent(location.pathname, entry.name || ''),
        };
        let currEntry = entry, nextEntry, nextAlias;
        while(
          _.isObjectLike(currEntry)
          && currEntry.category !== BOTTOMMOST_ENTRY_CATEGORY
          && Array.isArray(currEntry.entries)
          && currEntry.entries.length === 1
          && _.isObjectLike(nextEntry = currEntry.entries[0])
          && _.isString(nextAlias = nextEntry.name)
        ) {
          currEntry = nextEntry;
          const nextURLBasename = encodeURIComponent(nextAlias);
          to.pathname = joinURLComponent(to.pathname, nextURLBasename);
        }
        boundSetSelectedEntry(currEntry);
        return to;
      },
    };
  },
);

const AutoSelectRedirect = ({ getRedirectToEntry }) => (
  <Redirect to={getRedirectToEntry()} push={false}/>
);

export default connector(AutoSelectRedirect);
