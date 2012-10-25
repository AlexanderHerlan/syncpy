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
import ConfigParser
import watchdog
import paramiko
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from ftplib import FTP
import ftputil


# File names to ignore like temporary files forphotoshop saves or for ignoring GIT completely
ignore_list = ['_tmp', '.git', '.tmp']
# strings to remove from file operations
filter_list = ['.crdownload']

def win_to_lin_path(file_or_directory):
	
	if file_or_directory != "":
		path = file_or_directory[len(settings['local_path']):]
		path = path.replace("\\","/")
		path = settings['remote_path'] + path

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

def ignore_file(file_path, ignore_list):
	"return 1 (true) if any of the ignore_list are in file_path"

	if file_path.find('\\') != -1:
		file_path = file_path[len(settings['local_path'])+1:]
		path_elements = file_path.split('\\')

		if len(path_elements[len(path_elements)-1]) <= 4:
			return 1

	for word in ignore_list:
		if word in file_path:
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
	
	def __init__(self, ssh_client=None, ftp_client=None):
		if ssh_client is not None:
			self.ssh_client = ssh_client
			self.sftp_client = self.ssh_client.open_sftp()
		elif ftp_client:
			self.ftp_client = ftp_client

	def on_any_event(self, event):

		if not ignore_file(event.src_path, ignore_list):

			# Creating
			if type(event) == watchdog.events.FileCreatedEvent:
				localpath = filter_path(event.src_path, filter_list)
				remotepath = filter_path(win_to_lin_path(localpath), filter_list)
				# Wait some time before uploading the file because some 
				# apps do weird stuff to files as they're being saved.
				time.sleep(1)
				if file_exists(localpath):
					if settings['port'] == 22:
						self.sftp_client.put(localpath, remotepath)
					else:
						self.ftp_client.upload(localpath, remotepath)
					sync_logger.info('Created File: %s', remotepath)
					now = datetime.datetime.now()
					print now.strftime("%I:%M.%S %p -"),
					print 'Created: ' + remotepath[len(settings['remote_path'])+1:]
			if type(event) == watchdog.events.DirCreatedEvent:
				new_directory = win_to_lin_path(event.src_path)

				if settings['port'] == 22:
					self.sftp_client.mkdir(new_directory)
				else:
					self.ftp_client.mkdir(new_directory)

				sync_logger.info('Created Folder: %s', new_directory)
				now = datetime.datetime.now()
				print now.strftime("%I:%M.%S %p -"),
				print 'Created: ' + new_directory[len(settings['remote_path'])+1:]


			# Updating
			if type(event) == watchdog.events.FileModifiedEvent:
				localpath = event.src_path
				remotepath = win_to_lin_path(event.src_path)
				if settings['port'] == 22:
					if sftp_is_file(self.ssh_client, remotepath):
							self.sftp_client.put(localpath, remotepath)
				else:
					self.ftp_client.upload(localpath, remotepath)
				sync_logger.info('Updated: %s', remotepath)
				now = datetime.datetime.now()
				print now.strftime("%I:%M.%S %p -"),
				print 'Updated: ' + remotepath[len(settings['remote_path'])+1:]
			#if type(event) == watchdog.events.DirModifiedEvent:
				#print "DOESNT WORK ON WINDOWS SEE: https://github.com/gorakhargosh/watchdog/issues/92"  


			# Moving / Renaming
			if type(event) == watchdog.events.FileMovedEvent:
				if not ignore_file(event.dest_path, ignore_list):
					old_path = filter_path(win_to_lin_path(event.src_path), filter_list)
					new_path = filter_path(win_to_lin_path(event.dest_path), filter_list)
					cmd  = 'mv "' + old_path + '" "' + new_path + '"'
					self.ssh_client.exec_command(cmd)

					sync_logger.info('Moved: %s', old_path)
					now = datetime.datetime.now()
					print now.strftime("%I:%M.%S %p -"),
					print '  Moved: ' + old_path[len(settings['remote_path'])+1:]
					sync_logger.info('   to: %s', new_path)
					print '            -      to: ' + new_path[len(settings['remote_path'])+1:]
			if type(event) == watchdog.events.DirMovedEvent:
				if not ignore_file(event.dest_path, ignore_list):
					old_path = filter_path(win_to_lin_path(event.src_path), filter_list)
					new_path = filter_path(win_to_lin_path(event.dest_path), filter_list)
					cmd  = 'mv "' + old_path + '" "' + new_path + '"'
					self.ssh_client.exec_command(cmd)

					sync_logger.info('Moved: %s', old_path)
					now = datetime.datetime.now()
					print now.strftime("%I:%M.%S %p -"),
					print '  Moved: ' + old_path[len(remote_path)+1:]
					sync_logger.info('   to: %s', new_path)
					print '            -      to: ' + new_path[len(settings['remote_path'])+1:]


			# Deleting
			if type(event) == watchdog.events.FileDeletedEvent:
				old_file = win_to_lin_path(event.src_path)

				try:
					if settings['port'] == 22:
						self.sftp_client.remove(old_file)
					else:
						self.ftp_client.remove(old_file)
					
					sync_logger.info('Deleted: %s', old_file)
					now = datetime.datetime.now()
					print now.strftime("%I:%M.%S %p -"),
					print 'Deleted: ' + old_file[len(settings['remote_path'])+1:]
				except Exception as e:
					if settings['port'] == 22:
						if sftp_exists(self.sftp_client, old_file):
							self.ssh_client.exec_command('rm -r "' + old_file + '"')
						else:
							sync_logger.warning('Folder does not exist: %s', old_file)
					else:
						self.ftp_client.rmdir(old_file)

					sync_logger.info('Deleted Folder: %s', old_file)
					now = datetime.datetime.now()
					print now.strftime("%I:%M.%S %p -"),
					print 'Deleted: ' + old_file[len(settings['remote_path'])+1:]
			#if type(event) == watchdog.events.DirDeletedEvent:
				#print 'DOESNT WORK ON WINDOWS SEE: https://github.com/gorakhargosh/watchdog/issues/92'


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
			ssh_client.connect(hostname=settings['host'], port=settings['port'], username=settings['username'], pkey=key)
			sync_logger.info('RSA Authentication successful!')
			print "Authenticated ... ",
			return True
		except paramiko.SSHException, e:
			sync_logger.error('RSA Authentication failed!')

	sync_logger.warning('RSA key auth failed! Trying password login...')
	print "Using Password ... ",
	try:
		ssh_client.connect(hostname=settings['host'], port=settings['port'], username=settings['username'], password=settings['password'])
		sync_logger.info('Password login successful.')
		print "Authenticated ... ",
		return True
	except paramiko.AuthenticationException:
		sync_logger.error('Unable to authenticate!')
		sync_logger.error('Password missing or incorrect.')
		sync_logger.info('Please properly configure your sync.py header variables and try again.')
		return False


def load_config(project):
	if project in Config.sections():
		dict1 = {}
		options = Config.options(project)
		for option in options:
			try:
				if option == 'port':
					dict1[option] = int(Config.get(project, option))
				else:
					dict1[option] = Config.get(project, option)
				if dict1[option] == -1:
					print("skip: %s" % option)
			except:
				print("exception on %s!" % option)
				dict1[option] = None
		return dict1
	else:
		return False


def file_exists(PATH):
	if os.path.exists(PATH) and os.path.isfile(PATH) and os.access(PATH, os.R_OK):
		return True
	else:
		return False


""" 
-----------------------------------------------------------------------------------------------------------------------
- Application entry point for sync.py
-----------------------------------------------------------------------------------------------------------------------
"""

seperator = '-------------------------------------------------------------------------------'

if __name__ == "__main__":

	# Initialize python's logging facilities
	logging.basicConfig(format=' %(asctime)s %(levelname)s %(message)s')
	sync_logger = logging.getLogger(__name__)
	sync_logger.setLevel(logging.ERROR)

	# log SSH errors to file
	#paramiko.util.log_to_file('paramiko.log')
	#paramiko.util.logging.basicConfig(level=logging.ERROR)

	print seperator
	print 'Welcome to sync.py'

	# load external .config
	if file_exists('./sync.config'):
		# If the config file is found Initialize python's config parser
		Config = ConfigParser.ConfigParser()
		Config.read("sync.config")

		print 'Config file found...'

		if len(sys.argv) < 2:
			project_list = Config.sections()

			if len(project_list) > 1:
				print "Please choose a project: "
				print ' '
				
				i = 0
				for project in project_list:
					i += 1
					print str(i) + ' - ' + project

				print ' '

				project_select = raw_input('> ')
				if project_select != "":

					project_select = int(project_select) - 1

				#print str(len(project_list)) + ' ' + str(project_select)
				if project_select > len(project_list) - 1 or project_select < 0:
					print "Project not found."
					print 'See the included README.md file for more information.'
					print seperator
					sys.exit()
				else:
					settings = load_config(project_list[project_select])
					print "Loading project: " + project_list[project_select]
			else:
				if len(project_list) >= 1:
					print "Loading project: " + project_list[0]
					settings = load_config(project_list[0])
					project_list[0]
				else:
					print "No projects found in sync.config file.  Make sure it is configured properly"
					print 'See the included README.md file for more information.'
					print seperator
					sys.exit()
		else:
			settings = load_config(sys.argv[1])

			if settings != False:
				print "Loading project: " + sys.argv[1]
			else:
				print "Project name '" + sys.argv[1] + "' not found."
				print "Please make sure your sync.config file is configured properly"
				print 'See the included README.md file for more information.'
				print seperator
				sys.exit()
	else:
		print 'Config file \'sync.config\' is missing, or you do not have read persmission.'
		print 'See the included README.md file for more information.'
		print seperator
		sys.exit()


	print seperator

	# if SSH File transfer
	if settings['port'] == 22:
		ssh_client = paramiko.SSHClient()
		ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		if auth_user(ssh_client, settings['username']) == True:
			sync_logger.info('Connected to ssh://' + settings['username'] + '@' + settings['host'] + ':' + str(settings['port']) + settings['remote_path'])
			print 'Connected!'
			print ' Local Folder: '  + settings['local_path']
			print 'Remote Server: ssh://' + settings['username'] + '@' + settings['host'] + ':' + str(settings['port'])
			print 'Remote Folder: ' + settings['remote_path']
			event_handler = FileEventHandler(ssh_client=ssh_client)
			observer = Observer()
			observer.schedule(event_handler, settings['local_path'], recursive=True)
			observer.start()
			sync_logger.info('Watching ' + settings['local_path'])
			now = datetime.datetime.now()
			print now.strftime("\nNow syncing - %m/%d/%Y %I:%M %p %Ss - CTRL+C to exit.")
			print seperator
		else:
			sys.exit()
	elif settings['port'] == 21:
		ftp_client = ftputil.FTPHost(settings['host'], settings['username'], settings['password'])
		if ftp_client:
			print 'Connected!'
			print ' Local Folder: '  + settings['local_path']
			print 'Remote Server: ssh://' + settings['username'] + '@' + settings['host'] + ':' + str(settings['port'])
			print 'Remote Folder: ' + settings['remote_path']
			ftp_client.chdir(settings['remote_path'])
			event_handler = FileEventHandler(ftp_client=ftp_client)
			observer = Observer()
			observer.schedule(event_handler, settings['local_path'], recursive=True)
			observer.start()
			sync_logger.info('Watching ' + settings['local_path'])
			now = datetime.datetime.now()
			print now.strftime("\nNow syncing - %m/%d/%Y %I:%M %p %Ss - CTRL+C to exit.")
			print seperator


	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		if settings['port'] == 22:
			ssh_client.close()
		elif settings['port'] == 21:
			ftp_client.close()

		
		observer.stop()
	
	observer.join()