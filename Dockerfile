# syntax=docker/dockerfile:1

FROM python:3.10-slim

EXPOSE 5000

WORKDIR /app

RUN apt-get update && apt-get -y install build-essential cups libcups2-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY dm-print-web/build /app
COPY dm-print-web.py /app/app.py

ENV DM_PRINT_APP_DIRECTORY="/app"

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
