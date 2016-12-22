@echo off

REM add C:\Program Files\MySQL\MySQL Server 5.7\bin to path
set PATH=%PATH%;C:\Program Files\MySQL\MySQL Server 5.7\bin
set PATH=%PATH%;C:\Python27;C:\Python27\Scripts

set PATH=%PATH%;C:\spotipo\tools;C:\Program Files (x86)\Git\bin

REM check if python installed
where /q python.exe
IF ERRORLEVEL 1 (
    ECHO Python is missing. Ensure it is installed and placed in your PATH.
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B
) 
where /q pip
IF ERRORLEVEL 1 (
    python C:\spotipo\tools\get-pip.py

) 
where /q pip
IF ERRORLEVEL 1 (
    ECHO pip is missing. Ensure python scripts folder is added to path.
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B
) 

where /q mysql
IF ERRORLEVEL 1 (
    ECHO mysql is missing. Ensure MySQL server bin is added to path.
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B

) 

where /q git
IF ERRORLEVEL 1 (
    ECHO git is missing. something went wrong with install
    ECHO After fixing, rerun C:\spotipo\scripts\postinstall.bat
    pause
    EXIT /B
) 

cd C:\spotipo

REM create instance directory if not exists
IF NOT EXIST "C:\spotipo\instance" (mkdir "C:\spotipo\instance")
REM create logs directory if not exists
IF NOT EXIST "C:\spotipo\logs" (mkdir "C:\spotipo\logs")
REM create uploads directory if not exists
IF NOT EXIST "C:\spotipo\unifispot\static\uploads" (mkdir "C:\spotipo\unifispot\static\uploads")

IF NOT EXIST "C:\spotipo\instance\__init__.py" (copy NUL "C:\spotipo\instance\__init__.py" )


IF NOT EXIST "C:\spotipo\instance\config.py" ( 
    python C:\spotipo\scripts\winconfig.py
)

IF NOT EXIST "C:\spotipo\env\Scripts\activate.bat" (
    pip install virtualenv
    virtualenv C:\spotipo\env
)
call C:\spotipo\env\Scripts\activate.bat
REM install all binary packages
pip install C:\spotipo\tools\lxml-3.6.4-cp27-cp27m-win32.whl
pip install C:\spotipo\tools\mysql_python-1.2.5-cp27-none-win32.whl
REM install all required packages
pip install -r C:\spotipo\requirements\win.txt

IF NOT EXIST "C:\spotipo\migrations" ( 
    python C:\spotipo\manage.py db init 
)

python C:\spotipo\manage.py db migrate
python C:\spotipo\manage.py db upgrade
python C:\spotipo\manage.py init_data
python C:\spotipo\manage.py celery_get_notification


REM configure apache
IF NOT EXIST "C:\Apache24\modules\mod_wsgi.so" ( 
    copy C:\spotipo\tools\mod_wsgi.so C:\Apache24\modules
)
copy C:\spotipo\scripts\httpd.conf C:\Apache24\conf

REM check and install apache service
SC QUERY Apache24 > NUL
IF ERRORLEVEL 1060 GOTO INSTALLAPACHE
GOTO SKIPAPACHEINSTALL
:INSTALLAPACHE
REM installl apache2 service
C:\Apache24\bin\httpd.exe -k install -n "Apache24"
:SKIPAPACHEINSTALL
net stop Apache24 & net start Apache24


REM check and install celeryd service
SC QUERY celerydservice > NUL
IF ERRORLEVEL 1060 GOTO INSTALLCELERYD
GOTO SKIPCELERYDINSTALL
:INSTALLCELERYD
nssm install celerydservice C:\spotipo\scripts\celeryd.bat
:SKIPCELERYDINSTALL
net stop celerydservice & net start celerydservice



REM check and install celeryd service
SC QUERY celerybeatservice > NUL
IF ERRORLEVEL 1060 GOTO INSTALLCELERYBEAT
GOTO SKIPCELERYBEATINSTALL
:INSTALLCELERYBEAT
nssm install celerybeatservice C:\spotipo\scripts\celerybeat.bat
:SKIPCELERYBEATINSTALL
net stop celerybeatservice & net start celerybeatservice