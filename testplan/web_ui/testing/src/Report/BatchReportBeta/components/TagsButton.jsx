import React from 'react';
import { NavItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faTags } from '@fortawesome/free-solid-svg-icons';
import { connect } from 'react-redux';
import { TOOLBAR_BUTTON_CLASSES, BUTTONS_BAR_CLASSES } from '../styles';
import { mkGetUIIsShowTags } from '../state/uiSelectors';
import { setShowTags } from '../state/uiActions';

library.add(faTags);

const connector = connect(
  () => {
    const getIsShowTags = mkGetUIIsShowTags();
    return function mapStateToProps(state) {
      return {
        isShowTags: getIsShowTags(state),
      };
    };
  },
  function mapDispatchToProps(dispatch) {
    return {
      boundSetShowTags: isShow => dispatch(setShowTags(isShow)),
    };
  },
  function mergeProps(stateProps, dispatchProps) {
    const { isShowTags } = stateProps;
    const { boundSetShowTags } = dispatchProps;
    return {
      onClick: evt => {
        evt.stopPropagation();
        boundSetShowTags(!isShowTags);
      },
    };
  },
);

const TagsButton = ({ onClick }) => (
  <NavItem className={BUTTONS_BAR_CLASSES}>
    <FontAwesomeIcon key='toolbar-tags'
                     className={TOOLBAR_BUTTON_CLASSES}
                     icon={faTags.iconName}
                     title='Toggle tags'
                     onClick={onClick}
    />
  </NavItem>
);

export default connector(TagsButton);
