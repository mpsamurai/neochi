FROM ubuntu

RUN apt-get update && \
    apt-get install -y python3-dev python3-pip

COPY ./requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

WORKDIR /code
COPY ./neochi /code/neochi

ENV PYTHONPATH=$PYTHONPATH:/code

CMD ["pytest"]
