FROM python:3.11-bullseye

LABEL maintainer "Naoki Aoyama" \
  Description="speedtest_exporter docker image"

# tzdata
ENV DEBIAN_FRONTEND=noninteractive

ARG UID=1001
RUN useradd -m -u ${UID} speedtest
WORKDIR /home/speedtest

RUN \
  curl -s https://install.speedtest.net/app/cli/install.deb.sh | bash \
  && apt-get install speedtest

USER ${UID}
RUN mkdir -p                     /home/speedtest
ADD src/                         /home/speedtest
ADD pyproject.toml               /home/speedtest

RUN \
  curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
ENV PATH $PATH:/home/speedtest/.poetry/bin

RUN \
  poetry export --without-hashes -f requirements.txt -o requirements.txt
RUN pip3 install -r requirements.txt

EXPOSE 9353/tcp
ENTRYPOINT [ "python3", "/home/speedtest/speedtest/exporter.py" ]
