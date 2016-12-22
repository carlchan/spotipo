echo "---delete all files and folders----"
color 0f
cd ..
call env\Scripts\activate.bat
REM REM rd /s /q migrations_test 
REM REM del instance\database_test.db
REM echo "-----Initialize all DBs------------"
REM REM python test_manage.py db init
REM python test_manage.py db migrate
python test_manage.py db upgrade
cd tests
REM py.test  
py.test core\test_models.py::test_location -vv 
REM py.test -vv
color 0f
pause

