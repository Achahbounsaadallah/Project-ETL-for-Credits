FROM apache/airflow:2.9.0

USER root

RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    unixodbc \
    unixodbc-dev \
    apt-transport-https \
    ca-certificates \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# ✅ Installer Java pour Spark
RUN apt-get update && apt-get install -y openjdk-17-jdk
# ✅ Variable d'environnement Java
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
COPY jars/mssql-jdbc-13.4.0.jre11.jar /opt/airflow/jars/
USER airflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt