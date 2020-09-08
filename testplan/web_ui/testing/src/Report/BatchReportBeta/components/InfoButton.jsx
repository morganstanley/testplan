import React from 'react';
import { NavItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faInfo } from '@fortawesome/free-solid-svg-icons';
import { connect } from 'react-redux';
import { mkGetUIIsShowInfoModal } from '../state/uiSelectors';
import { setShowInfoModal } from '../state/uiActions';
import { TOOLBAR_BUTTON_CLASSES } from '../styles';
import { BUTTONS_BAR_CLASSES } from '../styles';

library.add(faInfo);

const connector = connect(
  () => {
    const getIsShowInfoModal = mkGetUIIsShowInfoModal();
    return function mapStateToProps(state) {
      return {
        isShowInfoModal: getIsShowInfoModal(state),
      };
    };
  },
  function mapDispatchToProps(dispatch) {
    return {
      boundSetShowInfoModal: isShow => dispatch(setShowInfoModal(isShow)),
    };
  },
  function mergeProps(stateProps, dispatchProps) {
    const { isShowInfoModal } = stateProps;
    const { boundSetShowInfoModal } = dispatchProps;
    return {
      toggleInfo: evt => {
        evt.stopPropagation();
        boundSetShowInfoModal(!isShowInfoModal);
      },
    };
  },
);

const InfoButton = ({ toggleInfo }) => (
  <NavItem className={BUTTONS_BAR_CLASSES}>
    <FontAwesomeIcon key='toolbar-info'
                     className={TOOLBAR_BUTTON_CLASSES}
                     icon={faInfo.iconName}
                     title='Info'
                     onClick={toggleInfo}
    />
  </NavItem>
);

export default connector(InfoButton);
