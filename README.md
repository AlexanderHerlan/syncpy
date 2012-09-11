Sync.py
=======

System Requirements / Dependencies 
------------

* Microsoft Windows Vista or above (Currently untested on Linux.  Feel free to make a pull request.  I might get around to it some day.)
* [Python 2.7.x](http://www.python.org/getit/releases/2.7/)
* [paramiko](http://www.lag.net/paramiko/)
* [watchdog](http://pypi.python.org/pypi/watchdog)


Understanding the .config file
------------------------------
When using sync.py you should rename the included "sync.config.example" file to "sync.config"
and fill it with your own settings.

Your .config file may contain multiple sections (or "Projects") denoted by [] square brackets.
Each section represents an individual project you are working on, with all the server settings required to sync to that server.
You can name projects whatever you would like as long as they are only alpha and numeric characters. (NO SPACES, NO SYMBOLS)

There should be settings for 3 example projects in the provided sync.config.example file.
An example of one project should look as follows:

	[MyProject2]
	local_path    = C:/dev/MyProject2
	remote_path   = /var/www/MyProject2
	host          = 10.0.0.18
	port          = 22
	username      = foo
	private_key   = 
	password      = bar

You only need 1 project minimum, but you can store as many as you'd like (not just the 3 I've included), as long as they follow this basic structure.


Breaking down the .config variables
-----------------------------------

The **local_path** is your working directory on your local system. Please note that you should use FORWARD ( / ) slashes even for Windows paths. So what would normally be:

	C:\dev\MyProject2

Must be entered into the settings file as:

	C:/dev/MyProject2

The **remote_path** is the path on your web server that you want to push files to.

The **host**, **port**, and **username** settings should all be set to that of your Linux user name and server you are attempting to sync to.

The **username** setting MUST always be set. It should be the user name of an account on the remote server you are connecting to, no matter what authentication scheme you are using.

The last 2 variables in this example are described below.


Authentication
--------------

You have 3 options for authentication. Please choose only one of the following:

First Option - If you are already running an SSH agent (like Pageant for Putty) with your RSA key properly loaded, you can leave both the **private_key** and **password** variables empty. Authentication should happen automatically as long as the **username** provided is correct. 

Second Option - You can put the path to your OpenSSH formated RSA key in the **private_key** variable if you prefer not to use an SSH Agent.  For example:

	private_key   = C:/Users/YourUsername/Documents/private-key.ppk

Third Option - (NOT RECOMMENDED for security reasons) You can put your SSH password associated with your **username** in the **password** variable as shown below:

	passowrd      = LetMeIn


Invoking the script
-------------------
Sync.py requires a valid sync.config file with at least one project entry.

You can invoke sync.py as follows:

	python sync.py

This will bring up a list of projects in your configuration file to choose from, or load the only project by default if only 1 exists.

Alternatively you invoke the script with the name of the project you would like to load as the first command line argument as follows:

	python sync.py MyProject2

If you have any questions feel free to tweet me: https://twitter.com/AlexHerlan