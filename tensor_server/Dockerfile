FROM python:3.12.4

RUN apt-get update \
 && apt-get -y --no-install-recommends upgrade \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
 
RUN apt-get install bash ca-certificates curl watch
RUN python -m pip install --upgrade pip
RUN mkdir -p /usr/apps/server

WORKDIR /usr/apps/server

COPY . /usr/apps/server

RUN pip install virtualenv Flask
RUN pip install -U sentence-transformers

CMD  ["/usr/local/bin/python", "/usr/apps/server/server.py"]
