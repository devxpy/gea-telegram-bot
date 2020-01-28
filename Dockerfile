FROM abiosoft/caddy as caddy
FROM library/python:3.8

RUN apt-get update && apt-get install -y wget tar

ENV WORKDIR /usr/src/app
RUN mkdir -p $WORKDIR
WORKDIR $WORKDIR

COPY --from=caddy /usr/bin/caddy .
COPY . $WORKDIR

CMD $WORKDIR/scripts/run-prod.sh
