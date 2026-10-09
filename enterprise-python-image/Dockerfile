FROM artifactory.eexchange.com/docker-main/python/python:3.11.14

ARG DEBIAN_FRONTEND=noninteractive
ARG MAVEN_VERSION=3.6.3
ARG MAVEN_URL=https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk \
    ca-certificates \
    curl \
    git \
    unzip \
    zip \
    tar \
 && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "${MAVEN_URL}" -o /tmp/maven.tgz \
 && tar -xzf /tmp/maven.tgz -C /opt \
 && ln -s /opt/apache-maven-${MAVEN_VERSION} /opt/maven \
 && ln -s /opt/maven/bin/mvn /usr/local/bin/mvn \
 && rm -f /tmp/maven.tgz

ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV MAVEN_HOME=/opt/maven
ENV PATH=${MAVEN_HOME}/bin:${JAVA_HOME}/bin:${PATH}

RUN java -version && mvn -version && python3 --version && pip3 --version

CMD ["tail", "-f", "/dev/null"]