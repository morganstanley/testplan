import React from 'react';
import ModalHeader from 'reactstrap/lib/ModalHeader';
import ModalFooter from 'reactstrap/lib/ModalFooter';
import ModalBody from 'reactstrap/lib/ModalBody';
import Modal from 'reactstrap/lib/Modal';
import Button from 'reactstrap/lib/Button';

import useReportState from '../hooks/useReportState';

/**
 * Return the help modal.
 * @returns {React.FunctionComponentElement}
 */
export default function HelpModal() {
  const [ isShowHelpModal, setShowHelpModal ] = useReportState(
    'app.reports.batch.isShowHelpModal',
    'setAppBatchReportShowHelpModal',
  );
  const toggle = () => setShowHelpModal(!isShowHelpModal);
  return (
    <Modal isOpen={isShowHelpModal} toggle={toggle} className='HelpModal'>
      <ModalHeader toggle={toggle}>Help</ModalHeader>
      <ModalBody>
        This is filter box help!
      </ModalBody>
      <ModalFooter>
        <Button color='light' onClick={toggle}>Close</Button>
      </ModalFooter>
    </Modal>
  );
}
