import React from 'react';
import { ModalHeader, ModalFooter, ModalBody, Modal, Button } from 'reactstrap';
import { connect } from 'react-redux';
import { mkGetUIIsShowHelpModal } from '../state/uiSelectors';
import { setShowHelpModal } from '../state/uiActions';

const connector = connect(
  () => {
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
      isShowHelpModal,
      toggleModal: () => boundSetShowHelpModal(!isShowHelpModal),
    };
  },
);

const HelpModal = ({ isShowHelpModal, toggleModal }) => (
  <Modal isOpen={isShowHelpModal} toggle={toggleModal} className='HelpModal'>
    <ModalHeader toggle={toggleModal}>Help</ModalHeader>
    <ModalBody>
      This is filter box help!
    </ModalBody>
    <ModalFooter>
      <Button color='light' onClick={toggleModal}>Close</Button>
    </ModalFooter>
  </Modal>
);

export default connector(HelpModal);
