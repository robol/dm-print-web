import React, { useEffect, useState } from 'react';
import PrinterList from './PrinterList';

async function loadPrinters() {
    const res = await fetch("/getPrinters", {
      credentials: 'include'
    })
    if (!res.ok) {
      throw new Error(`Printer status request failed (${res.status})`)
    }
    const data = await res.json()
    return data
  }

export default function AppBody() {
  const [printers, setPrinters] = useState([])
  const [printerStatusStale, setPrinterStatusStale] = useState(true)

  useEffect(() => {
    const refreshPrinters = async () => {
      try {
        const data = await loadPrinters()
        setPrinters(data["printers"] || [])
        setPrinterStatusStale(Boolean(data["stale"]))
      } catch (error) {
        console.error("Could not update printer status", error)
        setPrinterStatusStale(true)
      }
    }

    refreshPrinters()
    const id = setInterval(refreshPrinters, 10000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="App">
      <h1 className="display-2 my-5">WebPrint</h1>
      <div className="printers">
        <PrinterList
          printers={printers}
          statusStale={printerStatusStale}
        ></PrinterList>
      </div>
    </div>
  );
}
