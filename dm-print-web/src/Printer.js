import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faLocationDot, faPrint, faMessage } from '@fortawesome/free-solid-svg-icons'
import PrintDialog from './PrintDialog';
import { useState } from 'react';

export default function Printer({ printer, handlePrint }) {
    const [showDialog, setShowDialog] = useState(false)

    const onPrintSubmit = (confirm) => {
        console.log("OnPrintSubmit")
        setShowDialog(false)

        if (confirm) {
            console.log("printing")
            handlePrint();
        }
    }

    const showPrintDialog = () => {
        console.log("ok, showing print dialog")
        setShowDialog(true)
    }

    return <div className="printer col-12 col-md-6 col-lg-4 p-4">
        <PrintDialog printername={printer['printer-info']} show={showDialog} onSubmit={onPrintSubmit}></PrintDialog>
        <div className="border rounded p-2 text-start bg-light">
            <div className="flex d-flex flex-row justify-content-between">
                <div>
                    <FontAwesomeIcon icon={faPrint}></FontAwesomeIcon><strong> &nbsp;{printer['printer-info']}</strong><br></br>
                    <FontAwesomeIcon icon={faMessage}></FontAwesomeIcon> &nbsp;{printer['printer-state-message'] || <em>No status reported</em>}<br></br>
                    <FontAwesomeIcon icon={faLocationDot}></FontAwesomeIcon> &nbsp; { printer['printer-location']}
                </div>
                <div>
                    <button className="btn btn-primary" onClick={showPrintDialog}>Print</button>
                </div>
            </div>
        </div>
    </div>;
}