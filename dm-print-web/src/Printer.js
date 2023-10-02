import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faLocationDot, faPrint, faMessage } from '@fortawesome/free-solid-svg-icons'

export default function Printer({ printer, handlePrint }) {
    return <div className="printer col-12 col-md-6 col-lg-4 p-4">
        <div className="border rounded p-2 text-start bg-light">
            <div className="flex d-flex flex-row justify-content-between">
                <div>
                    <FontAwesomeIcon icon={faPrint}></FontAwesomeIcon><strong> &nbsp;{printer['printer-info']}</strong><br></br>
                    <FontAwesomeIcon icon={faMessage}></FontAwesomeIcon> &nbsp;{printer['printer-state-message'] || <em>No status reported</em>}<br></br>
                    <FontAwesomeIcon icon={faLocationDot}></FontAwesomeIcon> &nbsp; { printer['printer-location']}
                </div>
                <div>
                    <button className="btn btn-primary" onClick={handlePrint}>Print</button>
                </div>
            </div>
        </div>
    </div>;
}