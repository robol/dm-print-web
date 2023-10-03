# DM-PRINT-WEB

Web interface to print at the Department of Mathematics, University of Pisa.

## Development
Run the following commands to start the server in development:
```bash
python3 -mvenv env
. env/bin/activate
pip install -r requirements.txt
./app.py

# In a separate terminal
cd dm-print-web
DANGEROUSLY_DISABLE_HOST_CHECK=true npm start
```
