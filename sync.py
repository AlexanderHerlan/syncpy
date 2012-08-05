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
import datetime
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
local_path    = "C:\\dev\\nodechess"
# The remote folder on your web server to push to
remote_path   = "/home/orbitrix/www/snakebyte.net/nodechessdev"
# Your web server's host name and port
host          = "snakebyte.net"
port          = 22
# Your Linux (webserver ssh) username
username      = "orbitrix"

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
password      = ""
"""
-----------------------------------------------------------------------------------------------------------------------
                                    </End User Configuration Section>
                                     (Do not edit below this line)
-----------------------------------------------------------------------------------------------------------------------
"""

# File names to ignore like temporary files forphotoshop saves or for ignoring GIT completely
ignore_list = ['_tmp', '.git']
# strings to remove from file operations
filter_list = ['.crdownload']

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

def ignore_check(text, ignore_list):
    "return 1 (true) if any of the ignore_list are in text"
    for word in ignore_list:
        if word in text:
            #print now.strftime("%I:%M.%S %p -"),
            #print 'Ignored: ' + text[len(local_path)+1:]
            return 1
    return 0

def filter_path(path, filter):
    for word in filter:
        if path.endswith(word):
            path = path[:-len(word)]
    return path


#class FileEventHandler(FileSystemEventHandler):
class FileEventHandler(FileSystemEventHandler):
    
    def __init__(self, ssh_client):
        self.ssh_client = ssh_client
        self.sftp_client = self.ssh_client.open_sftp()


    def on_moved(self, event):
        #if not ignore_check(event.src_path, ignore_list):
        old_path = filter_path(win_to_lin_path(event.src_path), filter_list)
        new_path = filter_path(win_to_lin_path(event.dest_path), filter_list)
        cmd  = 'mv "' + old_path + '" "' + new_path + '"'
        self.ssh_client.exec_command(cmd)

        sync_logger.info('Moved: %s', old_path)
        now = datetime.datetime.now()
        print now.strftime("%I:%M.%S %p -"),
        print '  Moved: ' + old_path[len(remote_path)+1:]
        sync_logger.info('   to: %s', new_path)
        print '            -      to: ' + new_path[len(remote_path)+1:]
    

    def on_created(self, event):

        if not ignore_check(event.src_path, ignore_list):
            what = 'directory' if event.is_directory else 'file'
            localpath = filter_path(event.src_path, filter_list)
            remotepath = win_to_lin_path(localpath)

            if what == 'file':
                # Wait some time before uploading the file because some 
                # apps do weird stuff to files as they're being saved.
                time.sleep(1) 
                self.sftp_client.put(filter_path(localpath, filter_list), filter_path(remotepath, filter_list))

                sync_logger.info('Created File: %s', remotepath)
                now = datetime.datetime.now()
                print now.strftime("%I:%M.%S %p -"),
                print 'Created: ' + remotepath[len(remote_path)+1:]
            else:
                new_directory = win_to_lin_path(event.src_path)

                self.sftp_client.mkdir(new_directory)

                sync_logger.info('Created Folder: %s', new_directory)
                now = datetime.datetime.now()
                print now.strftime("%I:%M.%S %p -"),
                print 'Created: ' + new_directory[len(remote_path)+1:]


    def on_deleted(self, event):
        if not ignore_check(event.src_path, ignore_list):
            old_file = win_to_lin_path(event.src_path)

            try:
                self.sftp_client.remove(old_file)
                sync_logger.info('Deleted: %s', old_file)
                now = datetime.datetime.now()
                print now.strftime("%I:%M.%S %p -"),
                print 'Deleted: ' + old_file[len(remote_path)+1:]
            except Exception as e:
                if sftp_exists(self.sftp_client, old_file):
                    self.ssh_client.exec_command('rm -r "' + old_file + '"')
                    sync_logger.info('Deleted Folder: %s', old_file)
                    now = datetime.datetime.now()
                    print now.strftime("%I:%M.%S %p -"),
                    print 'Deleted: ' + old_file[len(remote_path)+1:]
                else:
                    sync_logger.warning('Folder does not exist: %s', old_file)

       
    def on_modified(self, event):
        if not ignore_check(event.src_path, ignore_list):
            localpath = event.src_path
            remotepath = win_to_lin_path(event.src_path)

            if sftp_is_file(self.ssh_client, remotepath):
                self.sftp_client.put(localpath, remotepath)
                sync_logger.info('Updated: %s', remotepath)
                now = datetime.datetime.now()
                print now.strftime("%I:%M.%S %p -"),
                print 'Updated: ' + remotepath[len(remote_path)+1:]


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
                print "Local authentication file found... ",
                agent_keys = agent.get_keys() + (local_key,)
        except Exception, e:
            sync_logger.warning('Failed loading local authentication key.')
    else:
        sync_logger.info('Using ssh-agent authentication key:')
        print "SSH Agent found ... ",

    for key in agent_keys:
        sync_logger.info('%s... ' % key.get_fingerprint().encode('hex'))
        try:
            ssh_client.connect(hostname=host, port=port, username=username, pkey=key)
            sync_logger.info('RSA Authentication successful!')
            print "Authenticated ... ",
            return True
        except paramiko.SSHException, e:
            sync_logger.error('RSA Authentication failed!')

    sync_logger.warning('RSA key auth failed! Trying password login...')
    print "Using Password ... ",
    try:
        ssh_client.connect(hostname=host, port=port, username=username, password=password)
        sync_logger.info('Password login successful.')
        print "Authenticated ... ",
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
    sync_logger.setLevel(logging.ERROR)

    # log SSH errors to file
    #paramiko.util.log_to_file('paramiko.log')
    #paramiko.util.logging.basicConfig(level=logging.ERROR)

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    print '-------------------------------------------------------------------------------'
    if auth_user(ssh_client, username) == True:
        sync_logger.info('Connected to ssh://' + username + '@' + host + ':' + str(port) + remote_path)
        print 'Connected!'
        print 'Remote Server: ssh://' + username + '@' + host + ':' + str(port)
        print 'Remote Folder: ' + remote_path
        event_handler = FileEventHandler(ssh_client=ssh_client)
        observer = Observer()
        observer.schedule(event_handler, local_path, recursive=True)
        observer.start()
        sync_logger.info('Watching ' + local_path)
        print ' Local Folder: '  + local_path
        now = datetime.datetime.now()
        print now.strftime("\nNow syncing - %m/%d/%Y %I:%M %p %Ss")
        print '-------------------------------------------------------------------------------'
    else:
        sys.exit()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ssh_client.close()
        observer.stop()
    
    observer.join()