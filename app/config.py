import os

# Mail server
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 534
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = os.environ.get('JPIS School')
MAIL_PASSWORD = os.environ.get('harshit18')

# administrator list
ADMINS = ['jpisvideotest@gmail.com']