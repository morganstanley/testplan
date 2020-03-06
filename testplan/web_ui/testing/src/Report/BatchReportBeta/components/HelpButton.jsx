import React from 'react';
import { NavItem } from 'reactstrap';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faQuestionCircle } from '@fortawesome/free-solid-svg-icons';
import { connect } from 'react-redux';
import { mkGetUIIsShowHelpModal } from '../state/uiSelectors';
import { setShowHelpModal } from '../state/uiActions';
import { TOOLBAR_BUTTON_CLASSES, BUTTONS_BAR_CLASSES } from '../styles';

library.add(faQuestionCircle);

const connector = connect(
  () =>  {
    const getIsShowHelpModal = mkGetUIIsShowHelpModal();
    return function mapStateToProps(state) {
      return {
        isShowHelpModal: getIsShowHelpModal(state),
      };
    };
  },
  function mapDispatchToProps(dispatch) {
    return {
      boundSetShowHelpModal: isShow => dispatch(setShowHelpModal(isShow)),
    };
  },
  function mergeProps(stateProps, dispatchProps) {
    const { isShowHelpModal } = stateProps;
    const { boundSetShowHelpModal } = dispatchProps;
    return {
      onClick: evt => {
        evt.stopPropagation();
        boundSetShowHelpModal(!isShowHelpModal);
      },
    };
  },
);

/**
 * Return the button which toggles the help modal.
 * @returns {React.FunctionComponentElement}
 */
const HelpButton = ({ onClick }) => (
  <NavItem className={BUTTONS_BAR_CLASSES}>
    <FontAwesomeIcon key='toolbar-question'
                     className={TOOLBAR_BUTTON_CLASSES}
                     icon={faQuestionCircle.iconName}
                     title='Help'
                     onClick={onClick}
    />
  </NavItem>
);

export default connector(HelpButton);
