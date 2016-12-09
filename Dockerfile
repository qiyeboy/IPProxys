FROM alpine:edge

RUN apk add --update python2 python2-dev py2-pip py2-lxml sqlite gcc musl-dev && \
	pip install --upgrade pip && \
	pip install requests chardet gevent && \
	apk del gcc python2-dev && \
	rm -fr /var/cache

COPY . /opt/IPProxyPool
WORKDIR /opt/IPProxyPool

EXPOSE 8080

CMD ["python", "IPProxys.py"]