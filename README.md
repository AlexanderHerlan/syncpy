Sync.py
=======

Understanding the .config file
------------------------------
When using sync.py you should rename the included sync.config.example file to sync.config
and fill it with your own settings.

The examples provides should look as follows:

	[MyProject2]
	local_path    = C:/dev/MyProject2
	remote_path   = /var/www/MyProject2
	host          = 10.0.0.18
	port          = 22
	username      = foo
	private_key   = 
	password      = bar


The local_path is your working directory on your local system. Please note that you should use FORWARD ( / ) slashes even for Windows path
So what would normally be:

	C:\dev\MyProject2

Must be entered into the settings file as:

	C:/dev/MyProject2

The remote_path is the path on your web server that you are testing your site on

The host, por, and username should all be those of your linux server you are attempting to sync to

You have 3 options for authentication. Please choose only one of the following:

1. If you are already running an ssh-agent (like Pageant for Putty) with your RSA key properly loaded, you can leave both of these variables with null strings. Authentication should be automatic as long as the above username is correct. 

2. You can put the path to your OpenSSH formated RSA key in the private_key variable below

	private_key   = C:/Users/YourUsername/Documents/private-key.ppk

3. (NOT RECOMMENDED for security reasons) You can put your SSH password associated with your username in the variable below

	Example: passowrd      = LetMeIn

Invoking the script
-------------------
Sync.py should be invoked as follows:

	python sync.py MyProject2

with the name of the "section" from your settings file you would like to load being passed as the first argument to the script.