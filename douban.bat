@echo off
rem 设置代码页为UTF-8并确保不显示命令本身
chcp 65001 > nul
rem 设置控制台字体以支持中文显示
rem 使用延迟环境变量扩展
setlocal enabledelayedexpansion

if "%1"=="" goto menu
if "%1"=="deploy" goto deploy
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="clean" goto clean
goto help

:menu
cls
echo ===== 豆瓣爬虫系统控制面板 =====
echo.
echo  请选择要执行的操作:
echo.
echo  [1] 部署基础服务 (构建镜像并启动数据库服务)
echo  [2] 启动爬虫节点
echo  [3] 启动系统 (不重新构建)
echo  [4] 停止系统
echo  [5] 清理数据
echo  [6] 退出
echo.
set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" goto deploy
if "%choice%"=="2" goto start_spider
if "%choice%"=="3" goto start
if "%choice%"=="4" goto stop
if "%choice%"=="5" goto clean
if "%choice%"=="6" exit /b 0
echo 无效的选项，请重新选择
timeout /t 2 /nobreak > nul
goto menu

:clean
cls
echo === 数据清理选项 ===
echo 警告：此操作将删除选定的数据！
echo.
echo 请选择要清理的数据:
echo [1] 清理所有数据
echo [2] 只清理 MongoDB 数据
echo [3] 只清理 Redis 数据
echo [4] 清理日志文件
echo [5] 清理爬虫状态文件
echo [6] 返回主菜单
echo.
set /p clean_choice=请输入选项 (1-6): 

if "!clean_choice!"=="1" goto clean_all
if "!clean_choice!"=="2" goto clean_mongodb
if "!clean_choice!"=="3" goto clean_redis
if "!clean_choice!"=="4" goto clean_logs
if "!clean_choice!"=="5" goto clean_state
if "!clean_choice!"=="6" goto menu
echo 无效的选项，请重新选择
timeout /t 2 /nobreak > nul
goto clean

:clean_all
echo === 清理所有数据 ===
set /p confirm=确定要清理所有数据吗? (y/n): 
if /i not "!confirm!"=="y" goto clean

echo 停止所有容器...
docker-compose down
timeout /t 5 /nobreak > nul

echo 删除所有数据卷...
docker volume rm douban_spider_mongodb-shard
docker volume rm douban_spider_mongodb-config
docker volume rm douban_spider_mongodb-router
docker volume rm douban_spider_redis
echo 所有数据卷已清理完成

echo 清理日志文件...
del /q /s logs\*.log >nul 2>&1
echo 日志文件已清理

echo 清理爬虫状态文件...
del /q /s data\*.state >nul 2>&1
echo 爬虫状态文件已清理
goto end

:clean_mongodb
echo === 只清理 MongoDB 数据 ===
set /p confirm=确定要清理 MongoDB 数据吗? (y/n): 
if /i not "%confirm%"=="y" goto clean

echo 停止所有容器...
docker-compose down
timeout /t 5 /nobreak > nul

echo 删除 MongoDB 数据卷...
docker volume rm douban_spider_mongodb-shard
docker volume rm douban_spider_mongodb-config
docker volume rm douban_spider_mongodb-router
echo MongoDB 数据卷已清理完成
goto end

:clean_redis
echo === 只清理 Redis 数据 ===
set /p confirm=确定要清理 Redis 数据吗? (y/n): 
if /i not "%confirm%"=="y" goto clean

echo 停止所有容器...
docker-compose down
timeout /t 5 /nobreak > nul

echo 删除 Redis 数据卷...
docker volume rm douban_spider_redis
echo Redis 数据卷已清理完成
goto end

:clean_logs
echo === 清理日志文件 ===
set /p confirm=确定要清理所有日志文件吗? (y/n): 
if /i not "%confirm%"=="y" goto clean

echo 清理日志文件...
del /q /s logs\*.log >nul 2>&1
echo 日志文件已清理完成
goto end

:clean_state
echo === 清理爬虫状态文件 ===
set /p confirm=确定要清理爬虫状态文件吗? (y/n): 
if /i not "%confirm%"=="y" goto clean

echo 清理爬虫状态文件...
del /q /s data\*.state >nul 2>&1
echo 爬虫状态文件已清理完成
goto end

:deploy
echo === 初始化系统目录 ===
mkdir logs 2>nul
mkdir data 2>nul
mkdir scripts 2>nul
echo 开始部署系统...
echo === 部署分布式爬虫系统基础服务 ===

echo 停止并清理现有容器...
docker-compose down
timeout /t 5 /nobreak > nul

echo 构建所有服务镜像...
docker-compose build --no-cache
timeout /t 5 /nobreak > nul

echo 启动 MongoDB 配置服务器...
docker-compose up -d mongodb-config
timeout /t 10 /nobreak > nul

echo 初始化配置服务器...
docker-compose up -d mongodb-config-init
timeout /t 15 /nobreak > nul

echo 启动分片服务器...
docker-compose up -d mongodb-shard
echo 等待分片服务器启动 (30秒)...
timeout /t 30 /nobreak > nul

echo 初始化分片服务器...
docker-compose up -d mongodb-shard-init
echo 等待分片服务器初始化 (20秒)...
timeout /t 20 /nobreak > nul

echo 启动路由服务器...
docker-compose up -d mongodb-router
timeout /t 10 /nobreak > nul

echo 添加分片到路由器...
docker-compose up -d mongodb-add-shard
timeout /t 10 /nobreak > nul

echo 启动 Redis 服务...
docker-compose up -d redis
timeout /t 5 /nobreak > nul

echo 检查服务状态...
docker-compose ps
goto end

:start_spider
echo === 启动爬虫节点 ===
echo 启动爬虫服务...
docker-compose up -d --force-recreate master worker1 worker2

echo 检查爬虫服务状态...
docker-compose ps master worker1 worker2

echo 检查爬虫日志...
for %%i in (master worker1 worker2) do (
    echo.
    echo === 服务 %%i 的日志 ===
    docker-compose logs %%i --tail=20
)
goto end

:help
echo 使用方法:
echo   douban.bat deploy        - 部署基础服务 (构建镜像并启动数据库服务)
echo   douban.bat spider        - 启动爬虫节点
echo   douban.bat start         - 启动系统 (不重新构建)
echo   douban.bat stop          - 停止系统
goto end

:start
echo === 启动分布式爬虫系统 ===
mkdir logs data scripts 2>nul
docker-compose up -d
goto end

:stop
echo === 停止分布式爬虫系统 ===
docker-compose down
goto end

:help
echo 使用方法:
echo   douban.bat deploy  - 部署系统 (构建镜像并启动所有服务)
echo   douban.bat start   - 启动系统 (不重新构建)
echo   douban.bat stop    - 停止系统
goto end

:end
echo.
echo 脚本执行完毕，按任意键退出...
pause > nul