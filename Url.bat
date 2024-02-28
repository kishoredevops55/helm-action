@echo off
setlocal

REM Define keywords and corresponding URLs
set "google_url=https://www.google.com"
set "youtube_url=https://www.youtube.com"
set "stackoverflow_url=https://stackoverflow.com"

REM Get the input keyword
set /p keyword="Enter a keyword (google, youtube, stackoverflow): "

REM Open the corresponding URL based on the keyword
if /i "%keyword%"=="google" (
    start "" "%google_url%"
) else if /i "%keyword%"=="youtube" (
    start "" "%youtube_url%"
) else if /i "%keyword%"=="stackoverflow" (
    start "" "%stackoverflow_url%"
) else (
    echo Invalid keyword. Please enter either google, youtube, or stackoverflow.
)

endlocal
