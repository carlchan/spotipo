from flask_qrcode import QRcode

qrcode = QRcode()



def configure(app):

    qrcode.init_app(app)