# run base image interactively and test commands:
# docker run -it --user root -e GRANT_SUDO=yes jupyter/scipy-notebook bash

FROM jupyter/scipy-notebook as temp_img

USER root

ARG SSH_PRIVATE_KEY
RUN sudo apt-get update \
    && apt-get -y install --no-install-recommends openssh-client \
    && mkdir /root/.ssh/ \
    && echo "${SSH_PRIVATE_KEY}" > /root/.ssh/id_rsa \
    && chmod 700 /root/.ssh/id_rsa \
    && touch /root/.ssh/known_hosts \
    && ssh-keyscan gitlab.nordstrom.com >> /root/.ssh/known_hosts

ARG CI_COMMIT_SHA
RUN git clone --recurse-submodules \
    git@gitlab.nordstrom.com:nordace/internal-tools/nordypy.git /nordypy \
    && cd /nordypy && git checkout ${CI_COMMIT_SHA}

######################################################################

FROM jupyter/scipy-notebook

USER root

ENV FLIT_ROOT_INSTALL=1

COPY --from=temp_img /nordypy /nordypy

RUN sudo apt-get -y update \
# && sudo apt-get -y install ... \ # if additional libraries are desired ...
  && sudo apt-get -y install --no-install-recommends \
      openssh-client \
  && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - \
  && sudo apt-get -y install --no-install-recommends nodejs npm \
  && npm install -g https://mvnrepo.nordstrom.net/nexus/content/groups/NPMgroup/awscreds/-/awscreds-1.1.1.tgz \
  && sudo apt-get autoremove -qy \
  && sudo apt-get autoclean -qy \
  && apt-get install -qy python3-pip \
  && sudo python3 -m pip install flit \
  && rm -rf /var/lib/apt/lists/* 


RUN cd /nordypy && flit install

RUN sudo apt-get autoremove -qy \
    && sudo apt-get autoclean -qy \
    && rm -rf /var/lib/apt/lists/* /nordypy

