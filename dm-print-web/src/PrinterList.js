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

    try {
        const res = await fetch('/printFile', {
            method: 'POST', body: formData, credentials: 'include'
        })

        if (!res.ok) {
            const msg = await res.json().catch(() => ({}))
            setErrorMsg(msg.result || "The print request failed. Please try again later.")
            setModalTitle("Error")
        }
        else {
            setErrorMsg(`The file has been submitted to ${p.name}`)
            setModalTitle("Printing in progress")
        }
        setShowModal(true)
    } catch (error) {
        console.error("Could not submit print job", error)
        setErrorMsg("The print service is temporarily unavailable. Please try again later.")
        setModalTitle("Error")
        setShowModal(true)
    }
}

export default function PrinterList({ printers, statusStale }) {
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
      <div className="col-12 text-start display-6 mb-3">Available printers</div>
        {statusStale &&
          <div className="col-12">
            <div className="alert alert-warning" role="alert">
              Printer status is temporarily unavailable or may be out of date.
            </div>
          </div>
        }
        {
            printers.map((p, j) => {
                const handlePrint = (file, options) => handlePrintAction(p, setShowModal, setErrorMsg, setModalTitle, file, options);
                return <Printer printer={p} handlePrint={handlePrint} key={`printer-${j}`}></Printer>
            })
        }
    </div></div></>
}
