#!/bin/bash

set -e

TAG="harbor.cs.dm.unipi.it/dm-print-web/dm-print-web"

( cd dm-print-web && npm run build )

sudo docker build -t ${TAG} .

echo -n "Should I push the image to the Docker Registry? [yn]: "
read ans
if [ "$ans" = "y" ]; then
  sudo docker push $TAG
fi
