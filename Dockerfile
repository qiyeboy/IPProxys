FROM alpine:edge

RUN apk add --update python2 python2-dev linux-headers musl musl-dev gcc py2-pip py2-lxml sqlite ;\
	pip install --upgrade pip && \
	pip install requests chardet web.py sqlalchemy gevent psutil ;\
	apk del gcc python2-dev && \
	rm -fr /var/cache

COPY . /opt/IPProxyPool
WORKDIR /opt/IPProxyPool

EXPOSE 8000

CMD ["python", "./IPProxy.py"]
