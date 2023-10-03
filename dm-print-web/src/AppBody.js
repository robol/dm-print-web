import React, { useEffect, useState } from 'react';
import PrinterList from './PrinterList';

async function loadPrinters() {
    const res = await fetch("/getPrinters")
    const data = await res.json()
  
    return data["printers"]
  }

export default function AppBody() {
  const [printers, setPrinters] = useState([])

  useEffect(() => {
      if (printers.length === 0) {
        (async () => setPrinters(await loadPrinters()))();
      }
  })

  // We use the following to periodically update the state of the printers
  useEffect(() => {
    const id = setInterval(async () => setPrinters(await loadPrinters()), 10000)    
    return () => clearInterval(id)
  })

  return (
    <div className="App">
      <h1 className="display-2 my-5">DM Print Web</h1>
      <div className="printers">
        <PrinterList printers={printers}></PrinterList>
      </div>
    </div>
  );
}