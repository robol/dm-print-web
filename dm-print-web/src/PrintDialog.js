import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button'
import { useState } from 'react'
import Form from 'react-bootstrap/Form';

export default function PrintDialog({ printername, show, onSubmit }) {
    const ModalTitle = printername

    const [numberOfCopies, setNumberOfCopies] = useState(1);
    const [sides, setSides] = useState('one-sided');
    const [file, setFile] = useState(null)

    const handleClose = () => {
        const options = {
            'copies': numberOfCopies, 
            'sides': sides
        }
        onSubmit(file, options)
    }

    const handleHide = () => {
        onSubmit(null, {})
    }

    const setFileHandler = (x) => {
      setFile(x.target.files[0])
    }

    return <Modal show={show} onHide={handleClose}>
        <Modal.Header closeButton>
          <Modal.Title>{ModalTitle}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
        <Form>
            <Form.Group className="mb-3" controlId="exampleForm.file">
              <Form.Label>PDF file</Form.Label>
              <Form.Control type="file" onChange={setFileHandler}></Form.Control>
            </Form.Group>
            <Form.Group className="mb-3" controlId="exampleForm.copies">
                <Form.Label>Number of copies</Form.Label>
                <Form.Control type="copies" value={numberOfCopies} onChange={(x) => setNumberOfCopies(x.target.value)}/>
            </Form.Group>
            <Form.Group className="mb-3" controlId="exampleForm.sides">
                <Form.Label>Sides</Form.Label>
                <Form.Select aria-label="Default select example" onChange={(x) => setSides(x.target.value)}>
                    <option value="one-sided">One sided</option>
                    <option value="two-sided-long-edge">Two-sided long edge</option>
                    <option value="two-sided-short-edge">Two-sided short edge</option>
                </Form.Select>
            </Form.Group>
        </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleHide}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleClose} disabled={file === null}>
            Print
          </Button>
        </Modal.Footer>
      </Modal>
}