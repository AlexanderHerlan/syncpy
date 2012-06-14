import os
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
import paramiko


local_path    = "C:\\dev\\snakebyte.net\\test\\"
remote_path   = "/home/orbitrix/www/snakebyte.net/test/"
host          = "snakebyte.net"
port          = 22
username      = "orbitrix"
private_key   = ""
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

def agent_auth(transport, username):

    try:
        mykey = paramiko.RSAKey.from_private_key_file(private_key)
    except Exception, e:
        mykey = None
        sync_logger.warning('Failed loading local authentication key.')

    agent = paramiko.Agent()

    if mykey != None:
        sync_logger.info('Using local authentication key.')
        agent_keys = agent.get_keys() + (mykey,)
    else:
        agent_keys = agent.get_keys()

        if len(agent_keys) == 0:
            sync_logger.warning('Failed loading ssh-agent key.')
            return
        else:
            sync_logger.info('Using ssh-agent authentication key.')
         

    for key in agent_keys:
        sync_logger.info('Attempting to authenticate with RSA key %s... ' % key.get_fingerprint().encode('hex'))
        try:
            transport.start_client()
            transport.auth_publickey(username, key)
            sync_logger.info('Success!')
            return
        except paramiko.SSHException, e:
            sync_logger.warning('Failed!', e)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(levelname)s %(message)s')
    sync_logger = logging.getLogger(__name__)
    sync_logger.setLevel(logging.DEBUG)

    # log SSH errors to file
    #paramiko.util.log_to_file('paramiko.log')
    #paramiko.util.logging.basicConfig(level=logging.ERROR)

    transport = paramiko.Transport((host, port))

    
    agent_auth(transport, username)


    if not transport.is_authenticated():
        sync_logger.warning('RSA key auth failed! Trying password login...')
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        sync_logger.info('Login successful.')
    else:

        
        transport.open_session()
        sftp = paramiko.SFTPClient.from_transport(transport)


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