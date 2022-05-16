# copy the dependencies file to the working directory
FROM python:3.7.2
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt