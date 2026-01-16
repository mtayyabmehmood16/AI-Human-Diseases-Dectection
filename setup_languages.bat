@echo off
echo Installing Flask-Babel...
pip install Flask-Babel

echo Extracting messages...
pybabel extract -F babel.cfg -o messages.pot .

echo Initializing Spanish translation...
if not exist "translations\es" (
    pybabel init -i messages.pot -d translations -l es
) else (
    echo Spanish translation already exists. Updating...
    pybabel update -i messages.pot -d translations -l es
)

echo Compiling translations...
pybabel compile -d translations

echo Done! Now edit translations/es/LC_MESSAGES/messages.po to add translations.
pause
