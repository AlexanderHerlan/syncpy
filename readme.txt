# The local folder on your computer to watch
'local_path':  "C:\\dev\\digitalmethod-flask",
# The remote folder on your web server to push to
'remote_path': "/root/flaskapp-dev",
# Your web server's host name and port
'host':        "69.122.56.18",
'port':        22,
# Your Linux (webserver ssh) username
'username':    "root",

# You have 3 options for authentication. Please choose only one of the following:
# 1) If you are already running an ssh-agent (like Pageant for Putty) with your RSA
#    key properly loaded, you can leave both of these variables with null strings.
#    Authentication should be automatic as long as the above username is correct. 

# 2) You can put the path to your OpenSSH formated RSA key in the private_key variable below
#    Example: private_key   = "C:\Users\Orbitrix\Documents\paramiko-private-key.ppk"
'private_key': "",
# 3) (NOT RECOMMENDED for security reasons) You can put your SSH password associated
#    with your username in the variable below
#    Example: passowrd      = "LetMeIn"
'password':    ""
