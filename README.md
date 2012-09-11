Sync.py
=======

Who this script is for
----------------------
This script is for Windows developers who would like to "auto-upload on save" from ANY program to a Linux development server.  This is convenient so that you don't have to rely on manually FTPing anything **ever**, and you don't have to use inferior built in solutions like Adobe Dreamweaver's FTP, which will only "Upload on save" files that you edit from within it.  Sync.py watches your file system for **any** changes from **any** application and automatically uploads the changes to your Linux development server.  Once you start the sync.py script, it just stays out of your way and keeps everything synced up.  Its a great lightweight replacement for Dropbox if you have your own development server and don't like relying on 3rd party solutions in your development work flow.  sync.py is also very secure using SSH and SFTP connections to do all of its magic.  It also supports RSA Key file and SSH-Agent authentication so you never have to rely on inferior passwords.

System Requirements / Dependencies 
------------

* Microsoft Windows Vista or above (Currently untested on Linux or WinXP.  Feel free to test it and let me know if it works.  I will get around to doing it some day though)
* [Python 2.7.x](http://www.python.org/getit/releases/2.7/)
* [paramiko](http://www.lag.net/paramiko/)
* [watchdog](http://pypi.python.org/pypi/watchdog)


Understanding the .config file
------------------------------
When using sync.py you should rename the included "[sync.config.example](syncpy/blob/master/sync.config.example)" file to "sync.config"
and fill it with your own settings.

Your sync.config example file should contain 3 sections (aka "Projects") denoted by square brackets like these: []  Each "Project"/section represents an individual folder on your local machine that you wish to sync with a folder on a remote server.  Each section also contains all the SSH/SFTP settings required to authenticate with that server. You can name projects whatever you would like as long as they are **only alpha and numeric** characters and contain **no spaces**, and **no symbols**.

There should be settings for 3 example projects in the provided [sync.config.example](syncpy/blob/master/sync.config.example) file.
An example of one project should look as follows:

	[MyProject2]
	local_path    = C:/dev/MyProject2
	remote_path   = /var/www/MyProject2
	host          = 10.0.0.18
	port          = 22
	username      = foo
	private_key   = 
	password      = bar

You only need 1 project minimum in your sync.config file for sync.py to work, but you can store as many as you would like (not just the 3 I've included), as long as they follow the basic structure shown above.


Breaking down the .config settings
-----------------------------------

The **local_path** setting is your working directory for your project on your local system. Please note that you should use FORWARD ( / ) slashes even for Windows paths. So what would normally be:

	C:\dev\MyProject2

Must be entered into the sync.config settings file as:

	C:/dev/MyProject2

The **remote_path** is the folder on your Linux web server that you want to push files to from the local_path.

The **host**, **port**, and **username** settings should all be set to your Linux user name and the connection info for the server you are attempting to sync to.

The **username** setting MUST always be set despite which authentication method you might be using, for more information see the next section.

The last 2 settings in this example are covered in the Authentication section below:


Authentication
--------------

You have 3 options for authentication. Please choose only one of the following:

**1) First Option** - (Highly recommended) If you are already running an SSH agent (like [Putty's Pageant.exe](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html)) with your RSA key properly loaded, you can leave both the **private_key** and **password** settings in your sync.config file empty. Authentication should happen automatically as long as the **username** provided is correct. 

**2) Second Option** - You can put the path to your OpenSSH formated RSA key in the **private_key** setting if you prefer not to use an SSH Agent.  For example:

	private_key   = C:/Users/Username/Documents/private-key.ppk

**3) Third Option** - (NOT RECOMMENDED for security reasons) You can put your Linux SSH password associated with your Linux **username** in the **password** setting as shown below:

	passowrd      = YourPasswordHere123


Invoking the script
-------------------
Sync.py **requires** a valid sync.config file to be in the same directory as the sync.py script itself.  It will need to have at least one "Project" entry as outline earlier in "Understanding the .config file" section of this README for the following commands to work.

You can invoke sync.py as follows:

	python sync.py

If you only have 1 entry in your sync.config settings file, it will load that by default.   Otherwise, running the script this way will bring up a multiple choice list of projects from your sync.config settings file.  Select the project you would like by entering the corresponding number next to the project name.

Alternatively, if you invoke the script with the name of the Project you would like to load from your sync.config settings file, you can bypass the multiple choice menu as follows:

	python sync.py MyProject2

(Note that in the sync.config settings file, the project name is surrounded by [brackets_like_these] but when referencing the project name at the command line you should not have them)

This will immediately load the specified project without delay. 



If you have any questions feel free to tweet me: https://twitter.com/AlexHerlan