@rem
@rem Copyright 2015 the original author or authors.
@rem
@rem Licensed under the Apache License, Version 2.0 (the "License");
@rem you may not use this file except in compliance with the License.
@rem You may obtain a copy of the License at
@rem
@rem      https://www.apache.org/licenses/LICENSE-2.0
@rem
@rem Unless required by applicable law or agreed to in writing, software
@rem distributed under the License is distributed on an "AS IS" BASIS,
@rem WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@rem See the License for the specific language governing permissions and
@rem limitations under the License.
@rem

@if "%DEBUG%" == "" @echo off
@rem ##########################################################################
@rem
@rem  RefactoringMiner startup script for Windows
@rem
@rem ##########################################################################

@rem Set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" setlocal

set DIRNAME=%~dp0
if "%DIRNAME%" == "" set DIRNAME=.
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%..

@rem Resolve any "." and ".." in APP_HOME to make it shorter.
for %%i in ("%APP_HOME%") do set APP_HOME=%%~fi

@rem Add default JVM options here. You can also use JAVA_OPTS and REFACTORING_MINER_OPTS to pass JVM options to this script.
set DEFAULT_JVM_OPTS=

@rem Find java.exe
if defined JAVA_HOME goto findJavaFromJavaHome

set JAVA_EXE=java.exe
%JAVA_EXE% -version >NUL 2>&1
if "%ERRORLEVEL%" == "0" goto execute

echo.
echo ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.
echo.
echo Please set the JAVA_HOME variable in your environment to match the
echo location of your Java installation.

goto fail

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE=%JAVA_HOME%/bin/java.exe

if exist "%JAVA_EXE%" goto execute

echo.
echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME%
echo.
echo Please set the JAVA_HOME variable in your environment to match the
echo location of your Java installation.

goto fail

:execute
@rem Setup the command line

set CLASSPATH=%APP_HOME%\lib\RefactoringMiner-3.0.4.jar;%APP_HOME%\lib\org.eclipse.jgit-6.8.0.202311291450-r.jar;%APP_HOME%\lib\slf4j-simple-2.0.11.jar;%APP_HOME%\lib\slf4j-api-2.0.11.jar;%APP_HOME%\lib\gen.jdt-3.0.0.jar;%APP_HOME%\lib\org.eclipse.jdt.core-3.36.0.jar;%APP_HOME%\lib\commons-text-1.11.0.jar;%APP_HOME%\lib\github-api-1.135.jar;%APP_HOME%\lib\java-diff-utils-4.12.jar;%APP_HOME%\lib\core-3.0.0.jar;%APP_HOME%\lib\JavaEWAH-1.2.3.jar;%APP_HOME%\lib\simmetrics-core-3.2.3.jar;%APP_HOME%\lib\commons-codec-1.16.0.jar;%APP_HOME%\lib\org.eclipse.core.resources-3.20.0.jar;%APP_HOME%\lib\org.eclipse.core.filesystem-1.10.200.jar;%APP_HOME%\lib\org.eclipse.text-3.13.100.jar;%APP_HOME%\lib\org.eclipse.core.expressions-3.9.200.jar;%APP_HOME%\lib\org.eclipse.core.runtime-3.30.0.jar;%APP_HOME%\lib\ecj-3.36.0.jar;%APP_HOME%\lib\commons-lang3-3.13.0.jar;%APP_HOME%\lib\jackson-annotations-2.13.0.jar;%APP_HOME%\lib\jackson-core-2.13.0.jar;%APP_HOME%\lib\jackson-databind-2.13.0.jar;%APP_HOME%\lib\commons-io-2.8.0.jar;%APP_HOME%\lib\classindex-3.10.jar;%APP_HOME%\lib\fastutil-8.3.1.jar;%APP_HOME%\lib\gson-2.8.2.jar;%APP_HOME%\lib\jgrapht-core-1.5.1.jar;%APP_HOME%\lib\org.eclipse.core.jobs-3.15.100.jar;%APP_HOME%\lib\org.eclipse.core.contenttype-3.9.200.jar;%APP_HOME%\lib\org.eclipse.equinox.app-1.6.400.jar;%APP_HOME%\lib\org.eclipse.equinox.registry-3.11.400.jar;%APP_HOME%\lib\org.eclipse.equinox.preferences-3.10.400.jar;%APP_HOME%\lib\org.eclipse.core.commands-3.11.100.jar;%APP_HOME%\lib\org.eclipse.equinox.common-3.18.200.jar;%APP_HOME%\lib\org.eclipse.osgi-3.18.600.jar;%APP_HOME%\lib\guava-18.0.jar;%APP_HOME%\lib\jheaps-0.13.jar;%APP_HOME%\lib\org.osgi.service.prefs-1.1.2.jar;%APP_HOME%\lib\osgi.annotation-8.0.1.jar


@rem Execute RefactoringMiner
"%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %REFACTORING_MINER_OPTS%  -classpath "%CLASSPATH%" org.refactoringminer.RefactoringMiner %*

:end
@rem End local scope for the variables with windows NT shell
if "%ERRORLEVEL%"=="0" goto mainEnd

:fail
rem Set variable REFACTORING_MINER_EXIT_CONSOLE if you need the _script_ return code instead of
rem the _cmd.exe /c_ return code!
if  not "" == "%REFACTORING_MINER_EXIT_CONSOLE%" exit 1
exit /b 1

:mainEnd
if "%OS%"=="Windows_NT" endlocal

:omega
