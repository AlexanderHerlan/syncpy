"""
sync.py simple folder synchronizer by Alexander Herlan (c) 2012
Description:  Automatically update files on your webserver when they are 
created modified or deleted locally.  The remote server is kept in sync Using 
SFTP and SSH commands. Great for automatic web development testing. Its an in-house 
way to securely replace dropbox for syncronization in some development cases. 
"""
import os
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
import paramiko

"""
-----------------------------------------------------------------------------------------------------------------------
                                        (Do not edit above this line)
                                        <User Configuration Section>
-----------------------------------------------------------------------------------------------------------------------
"""
# The local folder on your computer to watch
local_path    = "C:\\dev\\rolloff2"
# The remote folder on your web server to push to
remote_path   = "/var/wwwdev"
# Your web server's host name and port
host          = "10.0.0.20"
port          = 22
# Your Linux (webserver ssh) username
username      = "rocs"

# You have 3 options for authentication. Please choose only one of the following:

# 1) If you are already running an ssh-agent (like Pageant for Putty) with your RSA
#    key properly loaded, you can leave both of these variables with null strings.
#    Authentication should be automatic as long as the above username is correct. 

# 2) You can put the path to your OpenSSH formated RSA key in the private_key variable below
#    Example: private_key   = "C:\Users\Orbitrix\Documents\paramiko-private-key.ppk"
private_key   = ""

# 3) (NOT RECOMMENDED for security reasons) You can put your SSH password associated
#    with your username in the variable below
#    Example: passowrd      = "LetMeIn"
password      = "s8a7i3"
"""
-----------------------------------------------------------------------------------------------------------------------
                                    </End User Configuration Section>
                                     (Do not edit below this line)
-----------------------------------------------------------------------------------------------------------------------
"""

def win_to_lin_path(file_or_directory):
    
    if file_or_directory != "":
        path = file_or_directory[len(local_path):]
        path = path.replace("\\","/")
        path = remote_path + path

        return path


def sftp_exists(sftp, path):
    """os.path.exists for paramiko's SCP object
    """
    try:
        sftp.stat(path)
    except IOError, e:
        if e[0] == 2:
            return False
        raise
    else:
        return True


def sftp_is_file(ssh, path):
    cmd = '[ -f "' + path + '" ] && echo "File" || echo "Directory"';
    stdin, stdout, stderr = ssh.exec_command(cmd)
    result = stdout.read()
    result = result[:-1]

    #sync_logger.info("Command: %s", cmd)

    if result == "File":
        return True
    else:
        return False


#class FileEventHandler(FileSystemEventHandler):
class FileEventHandler(FileSystemEventHandler):
    
    def __init__(self, ssh_client):
        self.ssh_client = ssh_client
        self.sftp_client = self.ssh_client.open_sftp()


    def on_moved(self, event):
        if not ".git" in event.src_path:
            old_path = win_to_lin_path(event.src_path)
            new_path = win_to_lin_path(event.dest_path)
            cmd  = 'mv "' + old_path + '" "' + new_path + '"'
            self.ssh_client.exec_command(cmd)

            sync_logger.info('Moved: %s', old_path)
            sync_logger.info('   to: %s', new_path) 
    

    def on_created(self, event):
        if not ".git" in event.src_path:
            what = 'directory' if event.is_directory else 'file'
            localpath = event.src_path
            remotepath = win_to_lin_path(event.src_path)

            if what == 'file':
                # Wait some time before uploading the file because some 
                # apps do weird stuff to files as they're being saved.
                time.sleep(0.75) 
                self.sftp_client.put(localpath, remotepath)

                sync_logger.info('Created file: %s', remotepath)
            else:
                new_directory = win_to_lin_path(event.src_path)

                self.sftp_client.mkdir(new_directory)

                sync_logger.info('Created folder: %s', new_directory)


    def on_deleted(self, event):
        if not ".git" in event.src_path:
            old_file = win_to_lin_path(event.src_path)

            try:
                self.sftp_client.remove(old_file)
                sync_logger.info('Deleted file: %s', old_file)
            except Exception as e:
                if sftp_exists(self.sftp_client, old_file):
                    self.ssh_client.exec_command('rm -r "' + old_file + '"')
                    sync_logger.info('Deleted folder: %s', old_file)
                else:
                    sync_logger.warning('Folder does not exist: %s', old_file)

       
    def on_modified(self, event):
        if not ".git" in event.src_path:
            localpath = event.src_path
            remotepath = win_to_lin_path(event.src_path)

            if sftp_is_file(self.ssh_client, remotepath):
                self.sftp_client.put(localpath, remotepath)
                sync_logger.info('Updated file: %s', remotepath)


    def __del__(self):
        self.sftp_client.close()


def auth_user(ssh_client, username):

    agent = paramiko.Agent()
    agent_keys = agent.get_keys()

    if len(agent_keys) == 0:
        sync_logger.warning('Failed loading ssh-agent authentication key.')
        try:
            local_key = None
            local_key = paramiko.RSAKey.from_private_key_file(private_key)
            if local_key != None:
                sync_logger.info('Using local authentication key:')
                agent_keys = agent.get_keys() + (local_key,)
        except Exception, e:
            sync_logger.warning('Failed loading local authentication key.')
    else:
        sync_logger.info('Using ssh-agent authentication key:')

    for key in agent_keys:
        sync_logger.info('%s... ' % key.get_fingerprint().encode('hex'))
        try:
            ssh_client.connect(hostname=host, port=port, username=username, pkey=key)
            sync_logger.info('RSA Authentication successful!')
            return True
        except paramiko.SSHException, e:
            sync_logger.error('RSA Authentication failed!')

    sync_logger.warning('RSA key auth failed! Trying password login...')
    try:
        ssh_client.connect(hostname=host, port=port, username=username, password=password)
        sync_logger.info('Password login successful.')
        return True
    except paramiko.AuthenticationException:
        sync_logger.error('Unable to authenticate!')
        sync_logger.error('Password missing or incorrect.')
        sync_logger.info('Please properly configure your sync.py header variables and try again.')
        return False

""" 
-----------------------------------------------------------------------------------------------------------------------
- Application entry point for sync.py
-----------------------------------------------------------------------------------------------------------------------
"""
if __name__ == "__main__":

    logging.basicConfig(format=' %(asctime)s %(levelname)s %(message)s')
    #logging.basicConfig(format='%(message)s')

    sync_logger = logging.getLogger(__name__)
    sync_logger.setLevel(logging.DEBUG)

    # log SSH errors to file
    #paramiko.util.log_to_file('paramiko.log')
    #paramiko.util.logging.basicConfig(level=logging.ERROR)

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    if auth_user(ssh_client, username) == True:
        sync_logger.info('Connected to ssh://' + username + '@' + host + ':' + str(port) + remote_path)
        event_handler = FileEventHandler(ssh_client=ssh_client)
        observer = Observer()
        observer.schedule(event_handler, local_path, recursive=True)
        observer.start()
        sync_logger.info('Watching ' + local_path)
    else:
        sys.exit()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ssh_client.close()
        observer.stop()
    
    observer.join()