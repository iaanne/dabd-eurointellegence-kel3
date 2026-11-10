FROM docker.io/apache/iceberg-rest-fixture:1.10.1

# Image bawaan hanya membawa katalog JDBC tanpa driver Postgres. Driver
# ditambahkan ke classpath lewat `java -cp` di compose.yaml.
USER root

ADD https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar \
    /opt/jdbc/postgresql-42.7.4.jar
RUN chmod 644 /opt/jdbc/postgresql-42.7.4.jar \
    && chown -R iceberg:iceberg /opt/jdbc

USER iceberg