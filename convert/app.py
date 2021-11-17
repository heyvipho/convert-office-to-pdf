import os
import logging
import requests
import datetime
import hashlib
from urllib.parse import urlparse
from flask import Flask, request, send_file
from pantomime import FileName, normalize_mimetype, mimetype_extension
from pantomime.types import PDF

from convert.process import ProcessConverter
from convert.unoconv import UnoconvConverter
from convert.formats import load_mime_extensions
from convert.util import CONVERT_DIR
from convert.util import SystemFailure, ConversionFailure
from dotenv import load_dotenv


global dic

dic = {}

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("convert")
app = Flask("convert")
extensions = load_mime_extensions()
method = os.environ.get("CONVERTER_METHOD", "unoconv")
if method == "unoconv":
    converter = UnoconvConverter()
else:
    converter = ProcessConverter()
    converter.kill()
converter.unlock()


def getdotenv(env):
    try:
        #global env_path
        #load_dotenv(dotenv_path=env_path,override=True)
        load_dotenv(override=True)
        val = os.getenv(env)
        return val
    except (SystemFailure, Exception) as ex:
        log.warn("Error: %s", ex)
        return None

def setdotenv(key, value):  # string
    if key :
        if not value:
            value = '\'\''
        cmd = 'dotenv set -- '+key+' '+value  # set env variable
        os.system(cmd)


@app.route("/")
@app.route("/healthz")
@app.route("/health/live")
def check_health():
    try:
        if not converter.check_healthy():
            return ("BUSY", 500)
        return ("OK", 200)
    except Exception:
        log.exception("Converter is not healthy.")
        return ("DEAD", 500)


@app.route("/health/ready")
def check_ready():
    if converter.is_locked:
        return ("BUSY", 503)
    return ("OK", 200)


@app.route("/reset")
def reset():
    converter.kill()
    converter.unlock()
    return ("OK", 200)


@app.route("/convert", methods=["POST"])
def convert():
    upload_file = None
    if not converter.lock():
        return ("BUSY", 503)
    try:
        converter.prepare()
        timeout = int(request.args.get("timeout", 7200))
        upload = request.files.get("file")
        file_name = FileName(upload.filename)
        mime_type = normalize_mimetype(upload.mimetype)
        if not file_name.has_extension:
            file_name.extension = extensions.get(mime_type)
        if not file_name.has_extension:
            file_name.extension = mimetype_extension(mime_type)
        upload_file = os.path.join(CONVERT_DIR, file_name.safe())
        log.info("PDF convert: %s [%s]", upload_file, mime_type)
        upload.save(upload_file)
        out_file = converter.convert_file(upload_file, timeout)
        return send_file(out_file, mimetype=PDF)
    except ConversionFailure as ex:
        converter.kill()
        return (str(ex), 400)
    except (SystemFailure, Exception) as ex:
        converter.kill()
        log.warn("Error: %s", ex)
        return (str(ex), 500)
    finally:
        converter.unlock()




@app.route("/convert", methods=["GET"])
def convert2():
    upload_file = None
    if not converter.lock():
        return ("BUSY", 503)
    try:
        converter.prepare()
        timeout = int(request.args.get("timeout", 7200))

        fileUrl = request.args.get('fileSrc')
        hash_object = hashlib.sha256(fileUrl.encode('utf-8'))
        hashUrl = hash_object.hexdigest()
        if(getdotenv(hashUrl) != None):
            out_file = getdotenv(hashUrl)
            print("out_file")
            print(out_file)
            return send_file(out_file, mimetype=PDF)
        r = requests.get(fileUrl, allow_redirects=True)
        parseUrl = urlparse(fileUrl)
        file_name = str(datetime.datetime.now().timestamp()) + os.path.basename(parseUrl.path)
        upload_file = os.path.join(CONVERT_DIR, file_name)
        
        open(upload_file, 'wb').write(r.content)
        print(upload_file)

        out_file = converter.convert_file(upload_file, timeout)
        setdotenv(hashUrl, out_file)
        return send_file(out_file, mimetype=PDF)

       
    except ConversionFailure as ex:
        converter.kill()
        return (str(ex), 400)
    except (SystemFailure, Exception) as ex:
        converter.kill()
        log.warn("Error: %s", ex)
        return (str(ex), 500)
    finally:
        converter.unlock()

