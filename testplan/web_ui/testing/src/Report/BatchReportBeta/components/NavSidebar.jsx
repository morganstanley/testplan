import React from 'react';
import { ListGroup } from 'reactstrap';
import { css } from 'aphrodite';
import { connect } from 'react-redux';
import _ from 'lodash';
import {
  mkGetUIFilter,
  mkGetUISidebarWidthFirstAvailable,
} from '../state/uiSelectors';
import { setSidebarWidth } from '../state/uiActions';
import NavSidebarEntry from './NavSidebarEntry';
import Column from '../../../Nav/Column';
import * as filterStates from '../../../Common/filterStates';
import { isNonemptyArray } from '../../../Common/utils';
import { navListStyles } from '../styles';
import EmptyListGroupItem from './EmptyListGroupItem';

const BUTTON_LIST_CLASSES = css(navListStyles.buttonList);

const connector = connect(
  () => {
    const getFilter = mkGetUIFilter();
    const getFirstAvailableWidth = mkGetUISidebarWidthFirstAvailable();
    return function mapStateToProps(state) {
      return {
        filter: getFilter(state),
        width: getFirstAvailableWidth(state), // string of either em or px
      };
    };
  },
  function mapDispatchToProps(dispatch) {
    const onDragUnrestricted = px => dispatch(setSidebarWidth(px));
    return {
      onDrag: _.debounce(onDragUnrestricted, 12, { maxWait: 17 }),
    };
  },
);

const NavSidebar = ({ entries, filter, location, match, width, onDrag }) => {

  const entryFilter = React.useCallback(currEntry => {
    if(!_.isObject(currEntry)) return false;
    const { passed = 0, failed = 0, errored = 0 } = currEntry.counter || {};
    return !(
      (filter === filterStates.PASSED && passed === 0) ||
      (filter === filterStates.FAILED && (failed + errored) === 0)
    );
  }, [ filter ]);

  const links = React.useMemo(() => {
    const _links = !isNonemptyArray(entries) ? [] :
      entries.filter(entryFilter).map((entry, idx) => (
        <NavSidebarEntry entry={entry}
                         idx={idx + 1}
                         key={`${idx}`}
                         location={location}
                         match={match}
        />
      ));
    return _links.length ? _links : (<EmptyListGroupItem/>);
  }, [ entries, location, match, entryFilter ]);

  return (
    <Column width={width} handleColumnResizing={onDrag}>
      <ListGroup className={BUTTON_LIST_CLASSES}>
        {links}
      </ListGroup>
    </Column>
  );
};

export default connector(NavSidebar);
