FROM mariadb:10.4.13

ADD radios_bbdd_02122020.sql /docker-entrypoint-initdb.d
ADD my.cnf /etc/mysql/my.cnf
RUN chmod 644 /etc/mysql/my.cnf