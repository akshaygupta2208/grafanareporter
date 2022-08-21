FROM python:3.7-alpine

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories

# install chromedriver
RUN apk update
RUN apk add chromium chromium-chromedriver

WORKDIR /app

COPY requirements.txt /app
COPY ./src /app
RUN  pip3 install -r requirements.txt
CMD [ "python3", "main.py" ]
