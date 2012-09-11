Sync.py
=======

Who this script is for
----------------------
This script is for Windows developers who would like to have "upload on save" file transport functionality from **any** program on their local windows computer, straight to a Linux development server, automatically.  This script provides a convenient way to do fast paced iterative based testing and development, in areas such as web application design and server administration.  Sync.py makes it so that you don't have to rely on manually FTPing anything **ever**, and you don't have to use inferior built in solutions like Adobe Dreamweaver's FTP, which will only "Upload on save" files that you edit from within it, and that can sometimes interrupt your work.  Sync.py watches your file system for **any** changes from **any** application and automatically uploads the changes to your Linux development server, 100% silently, in the background of whatever application you might be using.

Sync.py is especially appealing if you have your own server and don't like relying on 3rd party cloud solutions like DropBox to help you test on your server.  Sync.py is self contained, only uses your resources (bandwidth, space, etc) and is very secure.  sync.py is so secure because it uses SSH and SFTP connections to tunnel all of its traffic.  It also supports [OpenSSH](http://en.wikipedia.org/wiki/OpenSSH) key file and [SSH-agent](http://en.wikipedia.org/wiki/Ssh-agent) authentication so you never have to rely on inferior password based logins.

Sync.py is a versatile solution because it works with most Linux distributions right out of the box using the power of the SSH protocol, and requires very few things setup on the Windows workstation side of things. Sync.py uses the secure SFTP functionality that is built right into the SSH protocol that virtually all Linux machines have.  This means you will never spend additional time setting up Samba or a standalone FTP service to do testing on a remote server you might not be familiar with.  No wasted energy making sure its tunneled securely.  No 3rd party apps or limitations.  Just get up and testing right away.

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

Your sync.config example file will contain 3 sections (aka "Projects") denoted by square brackets like these: []  Each "Project"/section represents an individual folder on your local machine that you wish to sync with a folder on a remote server.  Each section also contains all of the SSH/SFTP settings required to authenticate with that server. You can name projects whatever you would like as long as they are **only alpha and numeric** characters and contain **no spaces**, and **no symbols**.

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

(Note: I recommend deleting any of my example projects from your sync.config that you do not plan to edit with your own settings.)


Breaking down the .config settings
-----------------------------------

The **local_path** setting should be set to your working directory for the project on your local system you want to end up on your Linux server. Please note that you should use forward slashes ( / ) even for Windows paths. So what would normally be:

	C:\dev\MyProject2

Must be entered into the sync.config settings file as:

	C:/dev/MyProject2

The **remote_path** is the folder on your Linux web server that you want to push files to from the **local_path**.

The **host** must be the IP address or domain name of the remote server you are planning on syncing to.

The **port** must be set to the port number of the SSH service on the remote **host**.

The **username** setting must be set to a Linux user on the remote **host** that has read/write access to the **remote_path** you are planning to sync to. 


The last 2 settings in this example, "**priavte_key**" and "**password**", are covered in the Authentication section below:


Authentication
--------------

You have 3 options for authentication with the remote **host**. Please choose only one of the following:

**1) First Option** - (Highly recommended) If you are already running an [SSH-agent](http://en.wikipedia.org/wiki/Ssh-agent) (like [Putty's Pageant.exe](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html)) with your OpenSSH key properly loaded, you can leave both the **private_key** and **password** settings in your sync.config file empty. Authentication should happen automatically as long as the **username** setting provided is correct. 

**2) Second Option** - You can put the path to your OpenSSH formated RSA key in the **private_key** setting if you prefer not to use an SSH Agent.  For example:

	private_key   = C:/Users/Username/Documents/private-key.ppk

**3) Third Option** - (NOT RECOMMENDED for security reasons) You can put your Linux SSH password associated with your Linux **username** in the **password** setting as shown below:

	passowrd      = YourPasswordHere123


Invoking the script
-------------------
Sync.py **requires** a valid sync.config file to be in the same directory as the sync.py script itself before you run it.  It will need to have at least one "Project" entry as outlined earlier in "Understanding the .config file" section of this README for the following commands to work.

You can invoke sync.py as follows:

	python sync.py

If you only have 1 entry in your sync.config settings file, it will load that by default.   Otherwise, running the script this way will bring up a multiple choice list of projects from your sync.config settings file.  For example:

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

This will immediately load the specified project without delay. 



If you have any questions feel free to tweet me: https://twitter.com/AlexHerlan