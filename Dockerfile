# base image
FROM python:3.8-alpine  

#setting or changinf dir for working
WORKDIR /code
RUN apk add --no-cache mariadb-connector-c-dev ;\
    apk add --no-cache --virtual .build-deps \
        build-base \
        bash \
        mariadb-dev ;\
    pip install mysqlclient;\
    apk del .build-deps
#copy code from src loc -> dest 
COPY ./requirements.txt /code/requirements.txt
#update pip if necessary
RUN /usr/local/bin/python -m pip install --upgrade pip
#starting prereqisites
RUN pip install -r requirements.txt
#add code
COPY ./code /code
RUN rm /code/requirements.txt
ENTRYPOINT ["python"]
#specifing commad to execute
CMD [ "radios_api.py" ]