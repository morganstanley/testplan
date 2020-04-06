import React from 'react';
import ModalHeader from 'reactstrap/lib/ModalHeader';
import ModalFooter from 'reactstrap/lib/ModalFooter';
import ModalBody from 'reactstrap/lib/ModalBody';
import Modal from 'reactstrap/lib/Modal';
import Button from 'reactstrap/lib/Button';

import useReportState from '../hooks/useReportState';
import InfoTable from './InfoTable';

/**
 * Return the information modal.
 * @returns {React.FunctionComponentElement}
 */
export default function InfoModal() {
  const [ isShowInfoModal, setShowInfoModal ] = useReportState(
    'app.reports.batch.isShowInfoModal', 'setAppBatchReportShowInfoModal',
  );
  const toggle = () => setShowInfoModal(!isShowInfoModal);
  return (
    <Modal isOpen={isShowInfoModal}
           toggle={toggle}
           size='lg'
           className='infoModal'
    >
      <ModalHeader toggle={toggle}>Information</ModalHeader>
      <ModalBody>
        <InfoTable/>
      </ModalBody>
      <ModalFooter>
        <Button color='light' onClick={toggle}>Close</Button>
      </ModalFooter>
    </Modal>
  );
}
