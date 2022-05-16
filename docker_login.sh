#!/bin/bash
export PYTHONUNBUFFERED=true

login_timeout_seconds=90
timeout ${login_timeout_seconds} docker login -u oauth2accesstoken -p "$(/usr/bin/docker run --rm google/cloud-sdk:alpine gcloud auth print-access-token)" http://gcr.io
