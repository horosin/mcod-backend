FROM docker.elastic.co/beats/filebeat:6.7.0
COPY ./docker/filebeat/filebeat.yml /usr/share/filebeat/filebeat.yml
USER root
RUN mkdir /usr/share/filebeat/containers
RUN chown -R root /usr/share/filebeat/
RUN chmod -R go-w /usr/share/filebeat/


