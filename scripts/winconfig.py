import os
import uuid
import subprocess
import sys

mysqluser = raw_input('Enter hostname for MySQL server [root]:') or 'root'
mysqlpass = raw_input('Enter hostname for MySQL server [password]:') or 'password'
mysqldbname = raw_input('Enter hostname for MySQL server [spotipo]:') or 'spotipo'



with open('C:\\spotipo\\scripts\\instance_sample.py') as f:
    outfile = open('C:\\spotipo\\instance\\config.py','w')
    for line in f:
        if line.startswith('SQLALCHEMY_DATABASE_URI'):
            string = "SQLALCHEMY_DATABASE_URI = 'mysql://%s:%s@localhost/%s'"%(mysqluser,mysqlpass,mysqldbname)
            outfile.write(string)
        elif line.startswith('HASH_SALT') :
            string = "HASH_SALT ='%s'"%uuid.uuid4()
            outfile.write(string)
        else:
            outfile.write(line)
    outfile.close()

try:
    subprocess.check_output("mysql -u%s -p%s -e\"use %s\""%(mysqluser,mysqlpass,mysqldbname))
except:
    print "Databse not available,trying to create"
    try:
        subprocess.check_output("mysql -u%s -p%s -e\"create database %s\""%(mysqluser,mysqlpass,mysqldbname))
    except:
        print "Error occured while trying to create database"
        sys.exit()       

