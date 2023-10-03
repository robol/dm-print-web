#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 

import tempfile
import cups, os

from flask import Flask, request, send_from_directory, send_file
from flask_json import FlaskJSON, JsonError, json_response

from authentication import Authentication


app = Flask(__name__, static_folder=None)
auth = Authentication(app)

app.config['BASIC_AUTH_FORCE'] = True
app.config['JSON_ADD_STATUS'] = False
app.config['JSON_JSONP_OPTIONAL'] = False

# Configuration data: can be stati or given through environment variables
printserver = os.getenv("DM_PRINT_PRINTSERVER", "printserver.dm.unipi.it")
allowed_printers = os.getenv("DM_PRINT_ALLOWED_PRINTERS", "cdc11,cdcpp,cdcsd,cdclf,cdcpt,cdc6").split(",")
temporary_file_path = os.getenv("DM_PRINT_TMPPATH", "/tmp/")
app_directory = os.getenv("DM_PRINT_APP_DIRECTORY", "dm-print-web/build")

conn = cups.Connection(printserver)

@app.route("/getPrinters")
def getPrinters():
    printers = [ { **p, "name": k } for k,p in conn.getPrinters().items() if k in allowed_printers ]

    res = json_response(
        status_ = 200,
        printers = printers
    )
    res.headers.add('Access-Control-Allow-Origin', '*')

    return res

@app.route("/printFile", methods = ['POST'])
def printFile():
    file = request.files['file']
    filename = file.filename

    if not filename.endswith(".pdf"):
        res = json_response(result = "Only PDF files are allowed", status_ = 403)
    else:
        # Create a temporary folder
        newpath = os.path.join(temporary_file_path, tempfile.mktemp() + ".pdf")
        print("Saving temporary file in %s" % newpath)
        file.save(newpath)

        # Print the new file?
        conn.printFile(request.form.get('printer'), newpath, filename, {})

        os.remove(newpath)

        res = json_response(
            result = "OK"
        )

    res.headers.add('Access-Control-Allow-Origin', '*')
    return res

@app.route("/")
def index():
    return send_file(os.path.join(app_directory, 'index.html'))

@app.route("/<path:path>")
def build(path):
    return send_from_directory(app_directory, path)

if __name__ == "__main__":
    print("DM-PRINT-WEB 0.1")

    app.run(debug = (os.getenv("DM_PRINT_DEBUG", "1") == "1"))



