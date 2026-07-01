@echo off
echo ===================================================
echo Phantom Signal - Google Cloud and Firebase Deploy
echo ===================================================

echo.
echo STAGE 1: Logging into Google Cloud (Please check your web browser)...
call gcloud.cmd auth login

echo.
echo STAGE 2: Logging into Firebase CLI (Please check your web browser)...
call firebase login

echo.
echo STAGE 3: Deploying Streamlit container to Google Cloud Run...
call gcloud.cmd run deploy phantom-signal --source . --project osint-6bb27 --region asia-southeast1 --allow-unauthenticated

echo.
echo STAGE 4: Attaching Cloud Run container to Firebase Web Link...
call firebase deploy --only hosting

echo.
echo ===================================================
echo Deployment Complete! Check your public web link at:
echo https://osint-6bb27.web.app
echo ===================================================
pause
