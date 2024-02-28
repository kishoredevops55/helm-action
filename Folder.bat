@echo off
setlocal

rem Define keywords and corresponding paths
set "keyword1=documents"
set "path1=%USERPROFILE%\Documents"

set "keyword2=downloads"
set "path2=%USERPROFILE%\Downloads"

set "keyword3=pictures"
set "path3=%USERPROFILE%\Pictures"

rem Get input from user
set /p input="Enter keyword to open corresponding path: "

rem Check input against keywords and open corresponding path
if /i "%input%"=="%keyword1%" (
    start "" "%path1%"
) else if /i "%input%"=="%keyword2%" (
    start "" "%path2%"
) else if /i "%input%"=="%keyword3%" (
    start "" "%path3%"
) else (
    echo Keyword not recognized.
)

endlocal
