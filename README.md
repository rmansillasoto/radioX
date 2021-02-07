Proyecto API Python/Flask para Transcoding Radio streams a RTMP/IceCast

- Endpoints reciben y envían JSON para la configuración o las respuestas de la API: 
    - getAllRadios: Te muestra todas las radios configuradas.
    - getOneRadio/id: Te muestra la info de una radio.
    - addRadio: Añadimos una radio (de 1 a 4 codificaciones por radio, modos rtmp o Icecast)
        - RTMP output:
        ```
        {
        "ServiceName": "Radio3",
        "InputUrl": "http://radio3.rtveradio.cires21.com/radio3.mp3",
        "Outputs": "4",
        "OutputFormat": "rtmp",
        "AudioCodec": "aac",
        "AudioBitrate": "32,64,96,128",
        "AudioRate": "44100",
        "AudioProfile": "aac_he",
        "ServerIp": "10.40.80.157",
        "ServerPort": "1935",
        "ServerFolder": "/live",
        "ServerUser": "",
        "ServerPassword": ""
        }
        ```
        - Icecast output:
        ```
        {
        "ServiceName": "test_rtve_4",
        "InputUrl": "http://52.214.69.200:1935/live/test_rtve_3/playlist.m3u8",
        "Outputs": "4",
        "OutputFormat": "icecast",
        "AudioCodec": "mp3",
        "AudioBitrate": "48,64,128,256",
        "AudioRate": "44100",
        "AudioProfile": "",
        "ServerIp": "10.40.80.157",
        "ServerPort": "8000",
        "ServerFolder": "",
        "ServerUser": "user",
        "ServerPassword": "password"
        }
        ```
        
    - updateRadio/id: Editamos, actualizamos los datos de una radio.
        ```
        {
        "ServiceName": "Radio3",
        "InputUrl": "http://radio3.rtveradio.cires21.com/radio3.mp3",
        "Outputs": "4",
        "OutputFormat": "rtmp",
        "AudioCodec": "aac",
        "AudioBitrate": "32,64,96,128",
        "AudioRate": "44100",
        "AudioProfile": "aac_he",
        "ServerIp": "34.252.196.10",
        "ServerPort": "1935",
        "ServerFolder": "/live",
        "ServerUser": "",
        "ServerPassword": ""
        }
        ```

    - deleteRadio/id: Borramos el registro.
    - startRadio/id: Iniciamos la codificación de una radio con los parámetros configurados.
    - restartRadio/id: Reiniciamos el contenedor.
    - stopRadio/id: paramos la transcodificación
    - login: para conseguir el token de acceso, “username”: “radios”, “password”: “radios”
        ```
        {
	    "username": "radios",
	    "password": "radios"
        }
        ```
        - Devuelve una cosa tal que así:
            ```
            {
            "jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDY5MjIwMTcsImlhdCI6MTYwNjkxODQxNywibmJmIjoxNjA2OTE4NDE3LCJzdWIiOiJyYWRpb3MifQ.R7Kh9noCunu8AImWpy3Uuiy-kqIKiYKdNKZ5NnYNIjI",
            "exp": "Wed, 09 Dec 2020 14:13:37 GMT"
            }
            ```
        Hay que incluír éste Token en las peticiones que queramos hacer para que funcione. Se haría en la petición Auth -> BearerToken -> campo Token

- Parámetros (de momento):

    - "ServiceName": "Radio3",                                                     -> Nombre del Servicio
    - "InputUrl": "http://radio3.rtveradio.cires21.com/radio3.mp3",                -> url de orígen
    - "Outputs": "4",                                                              -> de 1 a 4 outputs por comando 
    - "OutputFormat": "rtmp",                                                      -> formato de salida RTMP / Icecast
    - "AudioCodec": "aac",                                                         -> códec de audio AAC (libfdk_aac) / MP3 (libmp3lame)
    - "AudioBitrate": "32,64,96,128",                                              -> Bitrates, de 1 a 4 valores se parados por comas, va relacionado con “outputs”
    - "AudioRate": "44100",                                                        -> Sample Rate
    - "AudioProfile": "aac_he",                                                    -> Solo para AAC, puede ser AAC_HE o AAC_HE_V2
    - "ServerIp": "10.40.80.157",                                                  -> IP del server en donde vamos a publicar el stream
    - "ServerPort": "1935",                                                        -> Puerto de publicación
    - "ServerFolder": "/live",                                                     -> En principio para rtmp, folder en donde publicamos.
    - "ServerUser": "",                                                            -> User para Icecast Server
    - "ServerPassword": ""                                                         -> Password para Icecast Server


- Contenedores -> radios_api:v1 (dockerfile within project's folder) & regsitry.overon.es/bbdd_radios_api:v1 (dockerfile inside mariadb folder)

    - API: contenedor de Python para ejecutar el código de la API. Usa el puerto TCP 4000 para recibir peticiones.
    - BBDD: base de datos MariaDB (SQL) para guardar los parámetros de cada radio. Puerto TCP 3306
    - PHPMYADMIN: de momento, para facilitar la configuración de la BBDD, puerto TCP 8080
    - NGINX_RTMP: para hacer de servidor RTMP, recibir los streams que publicamos y servirlos a clientes. Puerto TCP 1935
    - ICECAST: contenedor para levantar un servidor Icecast, poder recibir los streams publicados y poderlos servir. Puerto TCP 8000
    - PORTAINER: Para gestionar visualmente los contenedores que hay corriendo en la maquina por interfaz Web. Puerto TCP 9000

    Los contenedores de PHPMYADMIN, NGINX, ICECAST no deberían estar en el despliegue de producción. PORTAINER se podría dejar para poder operar contenedores de una manera visual hasta que haya un a GUI. El docker compose es el siguiente:
    
    ```
    version: "3"

    services:
    api:
        image: radios_api:v1
        container_name: radios_api
        restart: always
        ports:
        - 4000:4000
        volumes:
        - /var/run/docker.sock:/var/run/docker.sock
        links:
        - bbdd
    bbdd:
        image: bbdd_radios_api:v1
        container_name: radios_ddbb
        restart: always
        environment:
        - MYSQL_DATABASE=radios
        - MYSQL_ROOT_PASSWORD=root_password
        - MYSQL_USER=user
        - MYSQL_PASSWORD=pass
        volumes:
        - bbdd:/var/lib/mysql
        ports:
        - 3306:3306

    phpmyadmin:
        image: phpmyadmin/phpmyadmin:latest
        container_name: phpmydmin
        ports:
        - 8080:80
        environment:
        - PMA_ARBITRARY=1
        - PMA_HOST=bbdd
        depends_on:
        - bbdd

    nginx_rtmp:
        image: tiangolo/nginx-rtmp
        container_name: rtmp_server
        restart: on-failure
        ports:
        - 1935:1935

    icecast:
        image: moul/icecast
        container_name: icecast_server
        restart: on-failure
        environment:
        - ICECAST_SOURCE_PASSWORD=source_password
        - ICECAST_ADMIN_PASSWORD=admin_password
        - ICECAST_PASSWORD=admin_pass
        - ICECAST_RELAY_PASSWORD=relay_pass
        - ICECAST_HOSTNAME=10.40.80.157
        volumes:
        - logs:/var/log/icecast2
        - /etc/localtime:/etc/localtime:ro
        ports:
        - 8000:8000

    portainer:
        image: portainer/portainer-ce
        container_name: portainer
        restart: on-failure
        ports:
        - 9000:9000
        volumes:
        - /var/run/docker.sock:/var/run/docker.sock
        - portainer_data:/data

    volumes:
    bbdd:
    portainer_data:
    logs:
    ```

- Resultados:
    - Cuando se inicia la codificación de una radio la API te devuelve en JSON las URLS para escuchar:
        ```
        {
        "OK": "Radio_7_Radio3 Started Successfully.",
        "ListenUrls": "'rtmp://34.252.196.10:1935/live/Radio3_32k', 'rtmp://34.252.196.10:1935/live/Radio3_64k', 'rtmp://34.252.196.10:1935/live/Radio3_96k', 'rtmp://34.252.196.10:1935/live/Radio3_128k'"
        }
        ```

