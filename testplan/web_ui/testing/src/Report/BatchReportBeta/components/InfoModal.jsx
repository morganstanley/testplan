import React from 'react';
import { ModalHeader, ModalFooter, ModalBody, Modal, Button } from 'reactstrap';
import { connect } from 'react-redux';
import { mkGetUIIsShowInfoModal } from '../state/uiSelectors';
import { setShowInfoModal } from '../state/uiActions';
import InfoTable from './InfoTable';

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
      isShowInfoModal,
      toggleInfo: () => boundSetShowInfoModal(!isShowInfoModal),
    };
  },
);

const InfoModal = ({ isShowInfoModal, toggleInfo }) => (
  <Modal isOpen={isShowInfoModal}
         toggle={toggleInfo}
         size='lg'
         className='infoModal'
  >
    <ModalHeader toggle={toggleInfo}>Information</ModalHeader>
    <ModalBody>
      <InfoTable/>
    </ModalBody>
    <ModalFooter>
      <Button color='light' onClick={toggleInfo}>Close</Button>
    </ModalFooter>
  </Modal>
);

export default connector(InfoModal);
