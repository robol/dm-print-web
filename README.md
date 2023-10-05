# DM-PRINT-WEB

Web interface to print at the Department of Mathematics, University of Pisa.

## Development
Run the following commands to start the server in development:
```bash
# Install packages
sudo apt-get install libcups2-dev # or equivalent

# Run server
python3 -mvenv env
. env/bin/activate
pip install -r requirements.txt
export DM_PRINT_PREFERRED_URL_SCHEME=http
./app.py

# In a separate terminal
cd dm-print-web
DANGEROUSLY_DISABLE_HOST_CHECK=true npm start
```
