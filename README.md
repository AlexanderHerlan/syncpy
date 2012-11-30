Sync.py
=======

Who is this script for and what is it all about?
------------------------------------------------
This script is for web developers who would like to have "upload on save" file transport functionality from **any** program on their local computer, straight to any web development server with FTP or SFTP/SSH support.  This script provides a convenient way to do fast paced iterative based testing and development on a live remote server, or just for making quick edits to a live website.  Sync.py intends to be a superior replacement for Adobe Dreamweaver's Upload on Save FTP functionality, that works with any application/filetype and stays out of your way.  Sync.py watches your file system for **any changes** from **any application** and **automatically uploads** the changes to the remote machine of your choosing, 100% in the background and out of your way.

Sync.py can also be secure if you are using the SSH/SFTP connection option, it will tunnel all of its traffic over an encrypted connection.  It also supports [OpenSSH](http://en.wikipedia.org/wiki/OpenSSH) key file and [SSH-agent](http://en.wikipedia.org/wiki/Ssh-agent) authentication so you never have to rely on inferior password based logins, or storing passwords in configuration files.

**NEW (11/21/2012):**
Sync.py now compiles your .scss (SASS) files to .css, as well as CoffeeScript files to javascript, all before uploading!

**NEW (11/29/2012):**
Added "live_url" setting to settings file.  SyncPy will now open a web browser for the current project that its syncing.  A chrome plugin is being refined to provide live-reload like instant-reloading

System Requirements / Dependencies 
------------

* Microsoft Windows Vista or above or Linux (Untested on MacOSX, if anyone would like to do that for me let me know how it goes)
* [Python 2.7.x](http://www.python.org/getit/releases/2.7/)

You can use a python package manager like easy_install, pip or distribute (except for with PyCrypto on Windows) to install the following python packages: 

* [PyCrypto](https://www.dlitz.net/software/pycrypto/)  (This package can sometimes be problematic on windows.  It cannot be installed through most package management systems like easy_install pip etc.  I recommend installing a pre-compiled binary that matches the correct python 2.7 version [from here](http://www.voidspace.org.uk/python/modules.shtml#pycrypto).  Linux folks have it easy, just install it with any python package manager.)
* [paramiko](http://pypi.python.org/pypi/paramiko/1.8.0) Must be version 1.8+.
* [ftputil](http://ftputil.sschwarzer.net/trac)
* [watchdog](http://pypi.python.org/pypi/watchdog)
* [colorama](http://pypi.python.org/pypi/colorama)
* [pyScss](https://github.com/Kronuz/pyScss) Python SCSS (SASS) Compiler (currently only .scss support, no .sass support)
* [CoffeeScript](http://pypi.python.org/pypi/CoffeeScript) Python CoffeeScript Compiler
* [Twisted](http://pypi.python.org/pypi/Twisted)
* [autobahn](http://pypi.python.org/pypi/autobahn/0.5.9)

Understanding the .config file
------------------------------
When using sync.py you should rename the included "[sync.config.example](syncpy/blob/master/sync.config.example)" file to "sync.config"
and fill it with your own settings.

Your sync.config example file will contain 3 sections (aka "Projects") denoted by square brackets like these: []  Each "Project"/section represents an individual folder on your local machine that you wish to sync with a folder on a remote server.  Each section also contains all of the SSH/SFTP settings required to authenticate with that server. You can name projects whatever you would like as long as they are **only alpha and numeric** characters and contain **no spaces**, and **no symbols**.

There should be settings for 3 example projects in the provided [sync.config.example](syncpy/blob/master/sync.config.example) file.
An example of one project should look as follows:

	[MyProject2]
	live_url      = http://www.MyProject2.com/
	local_path    = C:\dev\MyProject2
	remote_path   = /var/www/MyProject2
	host          = 10.0.0.18
	port          = 22
	username      = foo
	private_key   = 
	password      = bar

You only need 1 project minimum in your sync.config file for sync.py to work, but you can store as many as you would like (not just the 3 I've included), as long as they follow the basic structure shown above.  

(Note: I recommend deleting any of my example projects from your sync.config that you do not plan to edit with your own settings.)


Breaking down the .config settings
-----------------------------------

The **live_url** setting is the webserver where you can reach the contents of **remote_path**

The **local_path** setting should be set to your working directory for the project on your local system.  This will be the folder that is pushed to the server any time a change is detected inside of it.

The **remote_path** is the folder on your Linux web server that you want to push files to from the **local_path**.

The **host** must be the IP address or domain name of the remote server you are planning on syncing to.

The **port** must be set to the port number of the SSH service on the remote **host**.

The **username** setting must be set to a Linux user on the remote **host** that has read/write access to the **remote_path** you are planning to sync to. 


The last 2 settings in this example, "**priavte_key**" and "**password**", are covered in the Authentication section below:


Authentication
--------------

You have 3 options for authentication with the remote **host**. Please choose only one of the following:

**1) First Option** - (Highly recommended) If you are already familiar with and running an [SSH-agent](http://en.wikipedia.org/wiki/Ssh-agent) (like [Putty's Pageant.exe](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html)) with your OpenSSH key properly loaded, you can leave both the **private_key** and **password** settings in your sync.config file empty. Authentication should happen automatically as long as the **username** setting provided is correct in matching with the key loaded into your Agent. 

**2) Second Option** - You can put the path to your OpenSSH formated RSA key in the **private_key** setting if you prefer not to use an SSH Agent.  Remember the **username** setting must be associated with the key you are specifying here.  You can specify which key to use as such:

	private_key   = C:/Users/Username/Documents/private-key.ppk

**3) Third Option** - (NOT RECOMMENDED for security reasons) You can put your Linux SSH password associated with your Linux **username** in the **password** setting as shown below:

	passowrd      = YourPasswordHere123

Passwords are inherently less secure than cryptographic key based authentication, AND you're going to save it in an unencrypted settings file?!?!?! Shame on you!  [Learn about SSH-Agent based authentication already.](http://the.earth.li/~sgtatham/putty/0.58/htmldoc/Chapter9.html)

Invoking the script
-------------------
Sync.py **requires** a valid sync.config file to be in the same directory as the sync.py script itself before you can successfully run it.  It will need to have at least one "Project" entry as outlined earlier in "Understanding the .config file" section of this README for the following commands to work.

Assuming you have already navigated to the folder containing sync.py in your Command Prompt or Terminal you can invoke sync.py as follows:

	python sync.py

If you only have 1 entry in your sync.config settings file, it will load that project by default and connect to the remote server automatically.   Otherwise, running the script this way will bring up a multiple choice list of projects from your sync.config settings file.  For example:

	Welcome to sync.py
	Config file found...
	Please choose a project:
	1 - MyProject1
	2 - MyProject2
	3 - MyOtherProjectLOL

	>

Select the project you would like to activate by entering the corresponding number next to the name of the project you want in the list, like this:

	> 2
	Loading project: MyProject2  

Alternatively, if you invoke the script with the name of a Project from your sync.config settings file as the first command line argument to the script, you can bypass the multiple choice menu as follows:

	python sync.py MyProject2

(Note that in the sync.config settings file, the project name is surrounded by [brackets_like_these] but when referencing the project name at the command line you should not have them)

This will immediately load the specified project without delay skipping over the multiple choice menu selection, even if other projects do exist. 


If you have any questions, comments or critiques, feel free to tweet me @AlexHerlan or fork me or poke me or ... or whatever it is you kids do these days.