import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button'
import React from 'react'
import Form from 'react-bootstrap/Form';

export default function PrintDialog({ printername, show, onSubmit }) {
    const ModalTitle = printername

    const handleClose = () => {
        onSubmit(true)
    }

    const handleHide = () => {
        onSubmit(false)
    }

    return <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>{ModalTitle}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
            Press the Print button below to select the file. 
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleHide}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleClose}>
            Print
          </Button>
        </Modal.Footer>
      </Modal>
}