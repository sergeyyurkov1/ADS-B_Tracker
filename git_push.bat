@echo off
cls

echo Cleaning up...
call rmdir /s /q .git
echo .git
call conda activate base
call python clean.py

echo init
call git init

echo git remote add origin
call git remote add origin https://github.com/sergeyyurkov1/ADS-B_Tracker.git

echo git add
call git add *

echo git commit
call git commit --all --message="commit"

echo git push
call git push --force origin main

pause
