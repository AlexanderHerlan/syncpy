"""
PySync by Alexander Herlan (c) 2012
Description:  Syncronize 2 folders over SSH/SFTP.  
Great for web development testing.
"""

import os
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
import paramiko

# The local folder on your computer to watch
local_path    = "C:\\dev\\snakebyte.net\\test\\"
# The remote folder on your web server to push to
remote_path   = "/home/orbitrix/www/snakebyte.net/test/"
# Your web server's host name and port
host          = "snakebyte.net"
port          = 22
# Your Linux (webserver ssh) username
username      = "orbitrix"

# You have 3 options for authentication and you only need to choose 1:

# 1) If you are already running an ssh-agent (like Pageant for Putty) with your SSH
#    key properly loaded, you can leave both of these variables with null strings.
#    Authentication should be automatic as long as the above username is correct. 

# 2) You can put the path to your OpenSSH format RSA key in the private_key variable below
private_key   = ""

# 3) (NOT RECOMMENDED for security reasons) You can put your SSH password in the variable below
password      = ""


def win_to_lin_path(file_or_directory):

    if file_or_directory != "":
        path = file_or_directory[len(local_path):]

        path = path.replace("\\","/")

        path = remote_path + path

        return path



class FileEventHandler(FileSystemEventHandler):
    def __init__(self, sftp):
        self.sftp = sftp


    def on_moved(self, event):
        what = 'directory' if event.is_directory else 'file'
        logging.info("Moved %s: from %s to %s", what, event.src_path, event.dest_path)
    
    def on_created(self, event):
        
        what = 'directory' if event.is_directory else 'file'
        localpath = event.src_path
        remotepath = win_to_lin_path(event.src_path)

        
        if what == 'file':
            self.sftp.put(localpath, remotepath)

            sync_logger.info('Created file: %s', remotepath)
        else:
            new_directory = win_to_lin_path(event.src_path)

            self.sftp.mkdir(new_directory)

            sync_logger.info('Created folder: %s', new_directory)

    def on_deleted(self, event):
        old_file = win_to_lin_path(event.src_path)

        try:
            self.sftp.remove(old_file)
            sync_logger.info('Deleted file: %s', old_file)
        except Exception as e:
            #logging.error('Caught exception while deleting:')
            self.sftp.rmdir(old_file)
            sync_logger.info('Deleted folder: %s', old_file)
            
            #logging.exception(e)
           
        logging.info("Deleted: %s", old_file)

        

    def on_modified(self, event):
        what = 'directory' if event.is_directory else 'file'
        logging.info("Modified %s: %s", what, event.src_path)

def auth_user(transport, username):

    agent = paramiko.Agent()
    agent_keys = agent.get_keys()

    if len(agent_keys) == 0:
        sync_logger.warning('Failed loading ssh-agent authentication key.')
        try:
            local_key = None
            local_key = paramiko.RSAKey.from_private_key_file(private_key)
            if local_key != None:
                sync_logger.info('Using local authentication key.')
                agent_keys = agent.get_keys() + (local_key,)
        except Exception, e:
            sync_logger.warning('Failed loading local authentication key.')
    else:
        sync_logger.info('Using ssh-agent authentication key.')

    for key in agent_keys:
        sync_logger.info('Attempting to authenticate with RSA key %s... ' % key.get_fingerprint().encode('hex'))
        try:
            transport.connect(username=username, pkey=key)
            sync_logger.info('RSA Authentication successful!')
        except paramiko.SSHException, e:
            sync_logger.error('RSA Authentication failed!', e)

    if not transport.is_authenticated():
        sync_logger.warning('RSA key auth failed! Trying password login...')
        try:
            transport.connect(username=username, password=password)
            sync_logger.info('Password login successful.')
            return True
        except paramiko.AuthenticationException:
            sync_logger.error('Unable to authenticate!')
            sync_logger.error('Password missing or incorrect.')
            sync_logger.info('Please properly configure your sync.py header variables and try again.')
            return False
    else:
        transport.open_session()
        return True

""" 
-----------------------------------------------------------------------------------------------------------------------
- Application entry point for sync.py
-----------------------------------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s')
    sync_logger = logging.getLogger(__name__)
    sync_logger.setLevel(logging.DEBUG)

    # log SSH errors to file
    #paramiko.util.log_to_file('paramiko.log')
    #paramiko.util.logging.basicConfig(level=logging.ERROR)

    ssh_client = paramiko.SSHClient()


    transport = paramiko.Transport((host, port))

    
    if auth_user(transport, username) == True:
        sftp = paramiko.SFTPClient.from_transport(transport)
        sync_logger.info('Connected to server.')
    else:
        sys.exit()

    path = sys.argv[1] if len(sys.argv) > 1 else local_path

    #event_handler = LoggingEventHandler()
    event_handler = FileEventHandler(sftp)

    observer = Observer()

    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sftp.close()
        transport.close()
        observer.stop()
    
    observer.join()