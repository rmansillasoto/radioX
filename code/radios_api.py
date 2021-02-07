from flask import Flask, request, jsonify, json
from flask_mysqldb import MySQL
from flask_jwt_simple import (JWTManager, jwt_required, create_jwt, get_jwt_identity)
import docker
import threading
from threading import Thread
import logging
from datetime import datetime, timedelta
import time
import collections
import re

app = Flask (__name__)
app.config['JSON_SORT_KEYS'] = False #Don´t Sort aphabetically JSON response

# mysql connecttion
app.config['MYSQL_HOST'] = 'radios_ddbb'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'raul'
app.config['MYSQL_PASSWORD'] = 'rauldb'
app.config['MYSQL_ROOT_PASSWORD'] = 'mysql_p3dx'
app.config['MYSQL_DB'] = 'radios'
mysql = MySQL(app) #Inicializamos bbdd

# settings
app.secret_key = 'mysecretkey'
app.config['JWT_SECRET_KEY'] = 'RADIOSAPI?admin' #Key for Token generation
jwt = JWTManager(app) #Inicializamos jwt para securizar por token

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-9s) %(message)s',)

# Global
ffmpegContainerVersion = "registry.overon.es/ffmpeg_alpine:v1"
ffprobeContainerVersion = "registry.overon.es/ffprobe_alpine:v1"
client = docker.from_env()

# SECURITY STUFF #
# Provide a method to create access tokens. The create_jwt()
# function is used to actually generate the token
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"Error": "Missing JSON in request"}), 400

    params = request.get_json()
    username = params.get('username', None)
    password = params.get('password', None)

    if not username:
        return jsonify({"Error": "Missing username parameter"}), 400
    if not password:
        return jsonify({"Error": "Missing password parameter"}), 400
    #Chequeamos que sólo podemos usar radios / radios como user/pass
    if username != 'radios' or password != 'radios':
        return jsonify({"Error": "Bad username or password"}), 401

    #Hacemos que el token tenga una validez por X tiempo (ahora, una semana desde el momento en el que se crea)
    dt = datetime.now() + timedelta(days=7)
    # Identity can be any data that is json serializable
    ret = {'jwt': create_jwt(identity=username), 'exp':dt}
    return jsonify(ret), 200

# Protect a view with jwt_required, which requires a valid jwt
# to be present in the headers.
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    return jsonify({'Granted Access': get_jwt_identity()}), 200


# ENDPOINTS API REST #

#GetAllRadios
@app.route('/getAllRadios', methods=['GET'])
@jwt_required
def getRadios(): 
    if request.method != 'GET':
        return
    cur = mysql.connection.cursor()
    query = """SELECT * FROM radios"""
    cur.execute(query)
    data = cur.fetchall()
    cur.close()
    radiosList = []
    for row in data:
        radios = collections.OrderedDict()
        radios['Id'] = row[0]
        radios['ServiceName'] = row[1]
        radios['InputUrl'] = row[2]
        radios['Outputs'] = row[3]
        radios['OutputFormat'] = row[4]
        radios['AudioCodec'] = row[5]
        radios['AudioBitrate'] = row[6]
        radios['AudioRate'] = row[7]
        radios['AudioProfile'] = row[8]
        radios['ServerIp'] = row [9]
        radios['ServerPort'] = row [10]
        radios['ServerFolder'] = row [11]
        radios['ServerUser'] = row [12]
        radios['ServerPassword'] = row [13]
        radios['Status'] = row [14]
        radios['ContainerID'] = row [15]
        radiosList.append(radios)
    return (json.dumps(radiosList))

#GetOneRadio
@app.route ('/getOneRadio/<string:id>', methods =['GET'])
@jwt_required
def getOneRadio(id):
    if request.method != 'GET':
        return
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM radios WHERE id = %s', [id])
    data = cur.fetchall()
    cur.close()
    #Si hay datos en la consulta del ID, devolvemos todos los valores que tiene ese ID.
    if len(data) >= 1:
        for row in data:
            radios = collections.OrderedDict()
            radios['Id'] = row[0]
            radios['ServiceName'] = row[1]
            radios['InputUrl'] = row[2]
            radios['Outputs'] = row[3]
            radios['OutputFormat'] = row[4]
            radios['AudioCodec'] = row[5]
            radios['AudioBitrate'] = row[6]
            radios['AudioRate'] = row[7]
            radios['AudioProfile'] = row[8]
            radios['ServerIp'] = row [9]
            radios['ServerPort'] = row [10]
            radios['ServerFolder'] = row [11]
            radios['ServerUser'] = row [12]
            radios['ServerPassword'] = row [13]
            radios['Status'] = row [14]
            radios['ContainerID'] = row [15]
        return (json.dumps(radios))
    else:
        if len(data) == 0:
            return jsonify({"Error": "TX with ID " +id+ " do not exist."}), 500    
               
#AddRadio
@app.route('/addRadio', methods=['POST'])   
@jwt_required
def addRadio():
    if request.method == 'POST':
        serviceName = request.json['ServiceName']
        cur = mysql.connection.cursor()
        cur.execute('SELECT id FROM radios WHERE ServiceName = %s', [serviceName])
        data = cur.fetchall()
        cur.close()
        #Chequeamos que no existe ID para el serviceName que queremos dar de alta, si no existe INSERT de los campos generando un nuevo ID (luego devolvemos el ID en la respuesta), else error ya existe. 
        if len(data) == 0:
            inputUrl = request.json['InputUrl']
            outputs = request.json['Outputs']
            outputFormat = request.json['OutputFormat']
            audioCodec = request.json['AudioCodec']
            audioBitrate = request.json['AudioBitrate']
            audioRate = request.json['AudioRate']
            audioProfile = request.json['AudioProfile']
            serverIp = request.json['ServerIp']
            serverPort = request.json['ServerPort']
            serverFolder = request.json['ServerFolder']
            serverUser = request.json['ServerUser']
            serverPassword = request.json['ServerPassword']
            status = 0
            containerId = ''
            
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO radios (ServiceName, InputUrl, Outputs, OutputFormat, AudioCodec, AudioBitrate, AudioRate, AudioProfile, ServerIp, ServerPort, ServerFolder, ServerUser, ServerPassword, Status, ContainerID) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                        (serviceName, inputUrl, outputs, outputFormat, audioCodec, audioBitrate, audioRate, audioProfile, serverIp, serverPort, serverFolder, serverUser, serverPassword, status, containerId))
            mysql.connection.commit()
            cur.execute('SELECT id FROM radios WHERE ServiceName = %s', [serviceName])
            data = str(cur.fetchone()[0])
            cur.close()
            return jsonify({"OK": "Radio "+ serviceName +" with id "+ data +" Added Succesfully"})
        else:       
            return jsonify({"Error": "Radio with ServiceName "+ serviceName + " already exist."}), 500

#UpdateRadio
@app.route ('/updateRadio/<string:id>', methods = ['PUT'])
@jwt_required
def updateRadio(id): 
    if request.method != 'PUT':
        return          
    #Check if ID already exists  
    cur = mysql.connection.cursor()
    cur.execute('SELECT id FROM radios WHERE id = %s', [id])
    data = cur.fetchall()
    cur.close()
    #Chequeamos que existen datos para este ID, si existe UPDATE de los campos del ID, else error no existe.
    if len(data) >= 1:
        serviceName = request.json['ServiceName']
        inputUrl = request.json['InputUrl']
        outputs = request.json['Outputs']
        outputFormat = request.json['OutputFormat']
        audioCodec = request.json['AudioCodec']
        audioBitrate = request.json['AudioBitrate']
        audioRate = request.json['AudioRate']
        audioProfile = request.json['AudioProfile']
        serverIp = request.json['ServerIp']
        serverPort = request.json['ServerPort']
        serverFolder = request.json['ServerFolder']
        serverUser = request.json['ServerUser']
        serverPassword = request.json['ServerPassword']
        cur = mysql.connection.cursor()
        cur.execute('UPDATE radios SET ServiceName= %s, InputUrl= %s, Outputs= %s, OutputFormat= %s, AudioCodec= %s, AudioBitrate= %s, AudioRate= %s, AudioProfile= %s, ServerIp= %s, ServerPort= %s, ServerFolder= %s, ServerUser= %s, ServerPassword= %s WHERE id = %s',
                    (serviceName, inputUrl, outputs, outputFormat, audioCodec, audioBitrate, audioRate, audioProfile, serverIp, serverPort, serverFolder, serverUser, serverPassword, id))
        mysql.connection.commit()
        cur.close()
        return jsonify({"OK": "Radio "+ serviceName +" with id "+ id +" Updated Succesfully"})
    else:           
        if len(data) == 0:
            return jsonify({"Error": "Radio with ID " +id+ " do not exist."}), 500

#DeleteRadio
@app.route ('/deleteRadio/<string:id>', methods = ['DELETE'])
@jwt_required
def deleteRadio(id):
    if request.method != 'DELETE':     
        return
     #Check if ID already exists
    cur = mysql.connection.cursor()
    cur.execute('SELECT id FROM radios WHERE id = %s', [id])
    data = cur.fetchall()
    cur.close()
    #Chequeamos que existen datos para este ID, si existe borramos, else error no existe.
    if len(data) >= 1:     
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM radios WHERE id = {0}' .format(id))
        mysql.connection.commit()
        cur.close()
        return jsonify({"OK": "Radio with id "+ id +" Deleted Succesfully"})
    else:
        if len(data) == 0:
            return jsonify({"Error": "RAdio with ID " +id+ " do not exist."}), 500       
    
#StartRadio
@app.route ('/startRadio/<string:id>', methods = ['POST'])
@jwt_required
def startRadio(id):
    if request.method != 'POST':   
        return
    #Check if ID already exists
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM radios WHERE id = %s', [id])
    data = cur.fetchall()
    cur.close()
    #Chequeamos que haya datos en la respuesta de la consulta que hemos hecho por ID, si hay datos chequearemos que el status es Stopped para poder iniciar el container
    #else, no está Stopped y no lo podemos iniciar. Si no hay data en la respuesta del ID, diremos que no existe.
    #Si status Stopped, y no hay containerID lanzaremos CreateRadioCommand para generar comando que pasaremos a client.conteainers.run, else container is Running or else existe ya un containerID. 
    #Si después de lanzar container hay containerID (se ha levantado el contenedor) update DDBB con status Running y containerID, else container error.
    if len(data) >= 1: 
        for row in data:
            #inputUrl = row[2]
            outputFormat = row[4]
            status = row[14]
            containerId= str(row[15])
        if status == 0:  
            if len(containerId) == 0:
                mode = outputFormat
                #Test Input con FFprobe, todavía experimental con streaming inputs
                #ffprobeTest = LaunchFfprobe (inputUrl, ffprobeContainerVersion, id)
                #ffprobeTest.start()
                #ffprobeTest.join()
                #if ffprobeTest.error:
                    #return jsonify({"Error": ""+ ffprobeTest.error +""}), 500
                #Create srt command
                RadioCommand = CreateRadioCommand (data, id, mode)
                RadioCommand.start()
                RadioCommand.join()
                #Launch srt Container
                container = client.containers.run(ffmpegContainerVersion, 
                            command= RadioCommand.command,
                            name= RadioCommand.name, 
                            remove=False,
                            restart_policy= {"Name": "always"},
                            network_mode="host",
                            volumes= {'/var/run/docker.sock':{'bind': '/var/run/docker.sock', 'mode': 'rw'}},
                            privileged= True,
                            stdin_open= False,
                            tty= True,
                            detach= True,
                            stdout= True)
                #Codigo para generar el container desde una clase, no funcionaba bien en SRT API, así que no lo usamos de momento.
                #srtRxContainer = CreateSrtContainer (srtContainerVersion, srtRxCommand.command, srtRxCommand.name, mode, id)
                #srtRxContainer.start()
                #time.sleep(1)
                #Mirar si se ha iniciado bien el container....no funciona y hay que mirarlo bien
                #container = client.containers.get(container.id)
                if container.id: 
                    cur = mysql.connection.cursor()
                    cur.execute('UPDATE radios SET containerId = %s, status = 1 WHERE id = %s',(container.short_id,id))
                    mysql.connection.commit()
                    cur.close() 
                    return jsonify({"OK": ""+ RadioCommand.name +" Started Successfully.", 
                                    "ListenUrls": ""+ str(RadioCommand.listenUrl) +""})        
                else:
                    return jsonify({"Error": "Container Initialization Error"}), 500
            else:
                return jsonify({"Error": "Radio with ID "+ id +" Already Exists"}), 500
        else:   
            return jsonify({"Error": "Radio with ID "+ id +" Already Started"}), 500
    else:     
        return jsonify({"Error": "Radio with ID " +id+ " do not exist."}), 500
            
#RestartRadio
@app.route ('/restartRadio/<string:id>', methods = ['POST'])
@jwt_required
def restartRadio(id):
    if request.method != 'POST':
        return  
    #Check if ID already exists and get some parameters
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM radios WHERE id = %s', [id])
    data = cur.fetchall()
    for row in data:
            status = row[14] 
            containerId = str(row[15])
    cur.close()
    #Chequeamos que haya datos en la respuesta de la consulta que hemos hecho por ID, si hay datos chequearemos que el status es Running para poder reiniciar el container
    #else, no está Running y no lo podemos reiniciar. Si no hay data en la respuesta del ID, diremos que no existe.
    if len(data) >= 1: 
        if status == 1:
            container = client.containers.get(containerId)
            container.restart()
            return jsonify({"OK": "Radio with ID "+ id +" Restarted Successfully"})   
        else:
            return jsonify({"Error": "Radio with ID "+ id +" is Stopped"}), 500
    elif len(data) == 0:
            return jsonify({"Error": "Radio with ID " +id+ " do not exist."}), 500  

#StopRadio        
@app.route ('/stopRadio/<string:id>', methods = ['POST'])
@jwt_required
def stopRadio(id):
    if request.method != 'POST':
        return  
    #Check if ID already exists
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM radios WHERE id = %s', [id])
    data = cur.fetchall()
    cur.close()
    #Chequeamos que haya datos en la respuesta de la consulta que hemos hecho por ID, si hay datos chequearemos que el status es Running para poder parar el container
    #else, no está Running y no lo podemos parar. Si no hay data en la respuesta del ID, diremos que no existe.
    if len(data) >= 1: 
        for row in data:
            status = row[14]
            containerId = str(row[15])
        if status == 1:
            container = client.containers.get(containerId)
            container.stop()
            container.remove()
            time.sleep(2)
            cur = mysql.connection.cursor()
            cur.execute('UPDATE radios SET containerId = "", status = 0  WHERE id = %s',[id])
            mysql.connection.commit()
            cur.close() 
            return jsonify({"OK": "Radio with ID "+ id +" Stopped Successfully"})
        else:
            container = client.containers.get(containerId)
            container.stop()
            container.remove()
            time.sleep(2)
            return jsonify({"Error": "Radio with ID "+ id +" Already Stopped"}), 500
    else:     
        if len(data) == 0:
            return jsonify({"Error": "Radio with ID " +id+ " do not exist."}), 500 

# Classes and functions #

#Clase en la que creamos el comando que se ejecutará en el contenedor de ffmpeg
class CreateRadioCommand(Thread):
    def __init__(self, data, id, mode):
        self.id = id
        self.data = data
        self.mode = mode
        super(CreateRadioCommand, self).__init__()
        self.command = None
        self.name = None 
        self.listenUrl = None
    
    def run(self):
        #gather parameters
        for row in self.data:
            serviceName = row[1]
            inputUrl = row[2]
            outputs = row[3]
            #outputFormat = row[4]
            audioCodec = row[5]
            audioBitrate = str(row[6])
            audioRate = str(row[7])
            audioProfile = row[8]
            serverIp = row [9]
            serverPort = row [10]
            serverFolder = row [11]
            serverUser = row [12]
            serverPassword = row [13]
        input = "-i '"+ inputUrl +"'"
        self.name = "Radio_"+self.id+"_"+serviceName+""
        #RTMP Output       
        if self.mode == "rtmp":   
            if outputs == 1:
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "flv"
                    encoding = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ audioBitrate +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding = "-acodec "+ audioCodec +" -b:a "+ audioBitrate +"k -ar "+ audioRate +""
                muxer = "-f "+ muxerFormat +""
                output = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ audioBitrate +"k'"
                self.command = " ".join((input, encoding, muxer, output))
                self.listenUrl = ""+ output +""
            elif outputs == 2:
                bitrates = audioBitrate.split(",")
                bitrate1 = bitrates[0]
                bitrate2 = bitrates[1]
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "flv"
                    encoding1 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                    encoding2 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding1 = "-acodec "+ audioCodec +" -b:a "+ bitrate1 +"k -ar "+ audioRate +""
                    encoding2 = "-acodec "+ audioCodec +" -b:a "+ bitrate2 +"k -ar "+ audioRate +""
                muxer = "-f "+ muxerFormat +""
                output1 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate1 +"k'"
                output2 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate2 +"k'"
                self.command = " ".join((input, encoding1, muxer, output1, encoding2, muxer, output2))
                self.listenUrl = ""+ output1 +","+ output2 +""
            elif outputs == 3:
                bitrates = audioBitrate.split(",")
                bitrate1 = bitrates[0]
                bitrate2 = bitrates[1]
                bitrate3 = bitrates[2]
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "flv"
                    encoding1 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                    encoding2 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                    encoding3 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate3 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding1 = "-acodec "+ audioCodec +" -b:a "+ bitrate1 +"k -ar "+ audioRate +""
                    encoding2 = "-acodec "+ audioCodec +" -b:a "+ bitrate2 +"k -ar "+ audioRate +""
                    encoding3 = "-acodec "+ audioCodec +" -b:a "+ bitrate3 +"k -ar "+ audioRate +""
                muxer = "-f "+ muxerFormat +""    
                output1 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate1 +"k'"
                output2 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate2 +"k'"
                output3 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate3 +"k'"
                self.command = " ".join((input, encoding1, muxer, output1, encoding2, muxer, output2, encoding3, muxer, output3))
                self.listenUrl = ""+ output1 +", "+ output2 +", "+ output3 +""
            elif outputs == 4:
                bitrates = audioBitrate.split(",")
                bitrate1 = bitrates[0]
                bitrate2 = bitrates[1]
                bitrate3 = bitrates[2]
                bitrate4 = bitrates[3]
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "flv"
                    encoding1 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                    encoding2 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                    encoding3 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate3 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                    encoding4 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate4 +"k -ar "+ audioRate +" -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding1 = "-acodec "+ audioCodec +" -b:a "+ bitrate1 +"k -ar "+ audioRate +""
                    encoding2 = "-acodec "+ audioCodec +" -b:a "+ bitrate2 +"k -ar "+ audioRate +""
                    encoding3 = "-acodec "+ audioCodec +" -b:a "+ bitrate3 +"k -ar "+ audioRate +""
                    encoding4 = "-acodec "+ audioCodec +" -b:a "+ bitrate4 +"k -ar "+ audioRate +""
                muxer = "-f "+ muxerFormat +""    
                output1 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate1 +"k'"
                output2 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate2 +"k'"
                output3 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate3 +"k'"
                output4 = "'"+ self.mode +"://"+ serverIp +":"+ serverPort + serverFolder +"/"+ serviceName +"_"+ bitrate4 +"k'"
                self.command = " ".join((input, encoding1, muxer, output1, encoding2, muxer, output2, encoding3, muxer, output3, encoding4, muxer, output4))
                self.listenUrl = ""+ output1 +", "+ output2 +", "+ output3 +", "+ output4 +""
        elif self.mode == "icecast":
            if outputs == 1:
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "adts"
                    encoding = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ audioBitrate +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding = "-acodec "+ audioCodec +" -b:a "+ audioBitrate +"k -ar "+ audioRate +" -content_type audio/mpeg"
                muxer = "-f "+ muxerFormat +""
                output = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ audioBitrate +"k'"
                outListen = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ audioBitrate +"k'"
                self.command = " ".join((input, encoding, muxer, output))
                self.listenUrl = ""+ outListen +""
            elif outputs == 2:
                bitrates = audioBitrate.split(",")
                bitrate1 = bitrates[0]
                bitrate2 = bitrates[1]
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "adts"
                    encoding1 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                    encoding2 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding1 = "-acodec "+ audioCodec +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                    encoding2 = "-acodec "+ audioCodec +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                muxer = "-f "+ muxerFormat +""
                output1 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate1 +"k'"
                output2 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate2 +"k'"
                outListen1 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate1 +"k'"
                outListen2 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate2 +"k'"
                self.command = " ".join((input, encoding1, muxer, output1, encoding2, muxer, output2))
                self.listenUrl = ""+ outListen1 +", "+ outListen2 +""
            elif outputs == 3:
                bitrates = audioBitrate.split(",")
                bitrate1 = bitrates[0]
                bitrate2 = bitrates[1]
                bitrate3 = bitrates[2]
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "adts"
                    encoding1 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                    encoding2 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                    encoding3 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate3 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding1 = "-acodec "+ audioCodec +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                    encoding2 = "-acodec "+ audioCodec +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                    encoding3 = "-acodec "+ audioCodec +" -b:a "+ bitrate3 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                muxer = "-f "+ muxerFormat +""
                output1 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate1 +"k'"
                output2 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate2 +"k'"
                output3 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate3 +"k'"
                outListen1 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate1 +"k'"
                outListen2 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate2 +"k'"
                outListen3 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate3 +"k'"
                self.command = " ".join((input, encoding1, muxer, output1, encoding2, muxer, output2, encoding3, muxer, output3))
                self.listenUrl = ""+ outListen1 +", "+ outListen2 +", "+ outListen3 +""
            elif outputs == 4:
                bitrates = audioBitrate.split(",")
                bitrate1 = bitrates[0]
                bitrate2 = bitrates[1]
                bitrate3 = bitrates[2]
                bitrate4 = bitrates[3]
                if audioCodec == "aac":
                    audioCodec = "libfdk_aac"
                    muxerFormat = "adts"
                    encoding1 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                    encoding2 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                    encoding3 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate3 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                    encoding4 = "-acodec "+ audioCodec +" -profile:a "+ audioProfile +" -b:a "+ bitrate4 +"k -ar "+ audioRate +" -content_type audio/aac -bsf:a aac_adtstoasc"
                elif audioCodec == "mp3":
                    audioCodec = "libmp3lame"
                    muxerFormat = "mp3"
                    encoding1 = "-acodec "+ audioCodec +" -b:a "+ bitrate1 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                    encoding2 = "-acodec "+ audioCodec +" -b:a "+ bitrate2 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                    encoding3 = "-acodec "+ audioCodec +" -b:a "+ bitrate3 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                    encoding4 = "-acodec "+ audioCodec +" -b:a "+ bitrate4 +"k -ar "+ audioRate +" -content_type audio/mpeg"
                muxer = "-f "+ muxerFormat +""
                output1 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate1 +"k'"
                output2 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate2 +"k'"
                output3 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate3 +"k'"
                output4 = "'"+ self.mode +"://"+serverUser +":"+serverPassword +"@"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate4 +"k'"
                outListen1 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate1 +"k'"
                outListen2 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate2 +"k'"
                outListen3 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate3 +"k'"
                outListen4 = "'http://"+ serverIp +":"+ serverPort +"/"+ serviceName +"_"+ bitrate4 +"k'"
                self.command = " ".join((input, encoding1, muxer, output1, encoding2, muxer, output2, encoding3, muxer, output3, encoding4, muxer, output4))
                self.listenUrl = ""+ outListen1 +", "+ outListen2 +", "+ outListen3 +", "+ outListen4 +"" 

#No usamos el FFprobe de momento
class LaunchFfprobe(Thread):
    
    def __init__(self, input, version, id):
        self.input = input
        self.version = version
        self.id = id
        super(LaunchFfprobe, self).__init__()
        self.error = None
        self.name = None
        
    def run(self):
        
        self.name = "FFprobe_Radio_"+self.id+""
        container = client.containers.run(self.version, 
                command= "-v quiet -timeout 500000 -print_format json -show_format -show_error -i "+self.input+"",
                remove=True,
                name= self.name,
                network_mode="host",
                volumes= {'/var/run/docker.sock':{'bind': '/var/run/docker.sock', 'mode': 'rw'}},
                privileged= False,
                stdin_open= False,
                tty= True,
                detach= True,
                stdout= True)
        time.sleep(1)
        for log in container.attach(stream=True):
            print(log)
            log = log.decode('utf-8')
            if re.search('Input/output error', log):
                self.error = "Input error. Maybe there is no active source."
   
# Start API port 4000 and 0.0.0.0 if you´re using docker          
if __name__ == '__main__':
    app.run(port = 4000, debug = True, host= "0.0.0.0")