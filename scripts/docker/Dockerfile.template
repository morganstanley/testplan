FROM python:%{PYTHON_VERSION}
MAINTAINER John Chiotis <john.chiotis@morganstanley.com>

ADD . /work
RUN pip install /work
ADD scripts/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
WORKDIR /work
ENTRYPOINT ["/entrypoint.sh"]
