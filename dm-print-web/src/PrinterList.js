import Printer from "./Printer"
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button'
import 'bootstrap/dist/css/bootstrap.css';
import { useState } from 'react';


async function handlePrintAction(p, setShowModal, setErrorMsg, setModalTitle, file, options) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('printer', p.name)
    formData.append('options', JSON.stringify(options))

    const res = await fetch('/printFile', {
        method: 'POST', body: formData, credentials: 'include'
    })

    if (res.status !== 200) {
        const msg = await res.json()
        setErrorMsg(msg.result)
        setModalTitle("Error")
        setShowModal(true)
    }
    else {
        setErrorMsg(`The file has been correctly printed on ${p.name}`)
        setModalTitle("Printing in progress")
        setShowModal(true)
    }
}

export default function PrinterList({ printers }) {
    const [showModal, setShowModal] = useState(false);
    const [ErrorMsg, setErrorMsg] = useState("");
    const [ModalTitle, setModalTitle] = useState("");

    const handleClose = () => setShowModal(false);

    return <>
    <div
      className="modal show"
      style={{ display: 'block', position: 'initial' }}
    >
      <Modal show={showModal} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>{ModalTitle}</Modal.Title>
        </Modal.Header>
        <Modal.Body>{ErrorMsg}</Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleClose}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
    <div className="container border-0 border p-3 border-secondary rounded"><div className="row">
      <div className="col-12 text-start display-6 mb-3">Instructions and available printers</div>
      <ul className="text-start mx-3">
        <li>Only PDF files can be printed.</li>
        <li>The status reported by the printers is not very reliable.</li>
      </ul>
        {
            printers.map((p, j) => {
                const handlePrint = (file, options) => handlePrintAction(p, setShowModal, setErrorMsg, setModalTitle, file, options);
                return <Printer printer={p} handlePrint={handlePrint} key={`printer-${j}`}></Printer>
            })
        }
    </div></div></>
}