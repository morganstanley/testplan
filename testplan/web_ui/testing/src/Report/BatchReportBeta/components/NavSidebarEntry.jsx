import React from 'react';
import { NavLink } from 'react-router-dom';
import { connect } from 'react-redux';
import { css } from 'aphrodite';
import { ListGroupItem } from 'reactstrap';
import _ from 'lodash';
import { mkGetUISelectedEntry, mkGetUIIsShowTags } from '../state/uiSelectors';
import { setSelectedEntry } from '../state/uiActions';
import {
  navUtilsStyles,
  UNDECORATED_LINK_STYLE,
  ACTIVE_LINK_CLASSES,
} from '../styles';
import { BOTTOMMOST_ENTRY_CATEGORY } from '../../../Common/defaults';
import { joinURLComponent } from '../../../Common/utils';
import TagList from '../../../Nav/TagList';
import NavEntry from '../../../Nav/NavEntry';

const SIDEBAR_LINK_CLASSES = css(
  navUtilsStyles.navButton,
  navUtilsStyles.navButtonInteract,
);

const connector = connect(
  () => {
    const getIsShowTags = mkGetUIIsShowTags();
    const getSelectedEntry = mkGetUISelectedEntry();
    return function mapStateToProps(state) {
      return {
        isShowTags: getIsShowTags(state),
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
    const { isShowTags, selectedEntry } = stateProps;
    const { boundSetSelectedEntry } = dispatchProps;
    const {
      idx,
      entry,
      location: currentLocation = {},
      match: {
        url: matchedUrl = '',
      } = {},
      entry: {
        name: entryName = '',
        tags: entryTags = {},
        uid: entryUid = '',
        category: entryCategory = '',
        status: entryStatus = '',
        counter: {
          passed: nPass = 0,
          failed: nFail = 0,
          error: nError = 0,
        } = {},
      },
    } = ownProps;
    return {
      entryName,
      entryTags,
      entryUid,
      entryCategory,
      entryStatus,
      nPass,
      isShowTags,
      currentLocation,
      nextPathname: joinURLComponent(matchedUrl, encodeURIComponent(entryName)),
      nFailOrError: nFail + nError,
      tabIndex: `${idx + 1}`,
      isActive: () => (
        _.isObject(selectedEntry) && selectedEntry.uid === entryUid
      ),
      onClick: () => {
        if(selectedEntry !== entry && _.isObject(entry)) {
          boundSetSelectedEntry(entry);
        }
      },
    };
  }
);

const NavSidebarEntry = ({
  entryName, entryTags, entryUid, entryCategory, entryStatus, nPass, onClick,
  isShowTags, nFailOrError, tabIndex, nextPathname, currentLocation, isActive
}) => {

  const nextLocation = React.useMemo(() => {
    if(entryCategory === BOTTOMMOST_ENTRY_CATEGORY) {
      return currentLocation;
    } else {
      return { ...currentLocation, pathname: nextPathname };
    }
  }, [ nextPathname, currentLocation, entryCategory ]);

  const MaybeTagList = React.useCallback(props => {
    if(!isShowTags || !entryTags) {
      return null;
    } else {
      return (
        <TagList entryName={entryName}
                 tags={entryTags}
                 {...props}
        />
      );
    }
  }, [ entryTags, entryName, isShowTags ]);

  const NavLinkAsTag = React.useCallback(props => {
    return (<NavLink {...props} />);
  }, []);

  return (
    <ListGroupItem tag={NavLinkAsTag}
                   data-uid={entryUid}
                   className={SIDEBAR_LINK_CLASSES}
                   activeClassName={ACTIVE_LINK_CLASSES}
                   style={UNDECORATED_LINK_STYLE}
                   tabIndex={tabIndex}
                   to={nextLocation}
                   isActive={isActive}
                   onClick={onClick}
    >
      <MaybeTagList/>
      <NavEntry type={entryCategory}
                status={entryStatus}
                name={entryName}
                caseCountPassed={nPass}
                caseCountFailed={nFailOrError}
      />
    </ListGroupItem>
  );
};

export default connector(NavSidebarEntry);
