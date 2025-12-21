@echo off
REM Setup script for the scraper (Windows)

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Installing Playwright browsers (Chromium)...
playwright install chromium

echo.
echo Setup complete!
echo You can now run the scraper with: python src\run_scraper.py
pause