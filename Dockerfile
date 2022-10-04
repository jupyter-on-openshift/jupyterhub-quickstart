FROM centos/python-38-centos7:latest

LABEL io.k8s.display-name="JupyterHub" \
      io.k8s.description="JupyterHub." \
      io.openshift.tags="builder,python,jupyterhub" \
      io.openshift.s2i.scripts-url="image:///opt/app-root/builder"

USER root
RUN yum update -y && yum autoremove -y && yum clean all

WORKDIR /tmp
COPY . /tmp/src

RUN chown -R 1001 /tmp/src && \
    chgrp -R 0 /tmp/src && \
    chmod -R g+w /tmp/src && \
    mv /tmp/src/.s2i/bin /tmp/scripts

USER 1001

ENV NPM_CONFIG_PREFIX=/opt/app-root \
    PYTHONPATH=/opt/app-root/src

RUN /tmp/scripts/assemble
CMD [ "/opt/app-root/builder/run" ]
