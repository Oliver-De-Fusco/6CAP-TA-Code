call .venv\Scripts\activate.bat

set /p filename= "Filename : "

for /f "tokens=1-6 delims=:/ " %%a in ("%date% %time%") do (
    set "timestamp=%%c_%%b_%%a_%%d_%%e_%%f"
)

set "timestamp=%timestamp: =%"

jupyter nbconvert "%filename%.ipynb" --to html --output "%filename%_%timestamp%.html" 