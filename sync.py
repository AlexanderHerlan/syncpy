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
import ftputil
import json
from colorama import init as color_init
from colorama import Fore, Back, Style
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from ftplib import FTP
import scss
import coffeescript
import webbrowser

from twisted.internet import reactor
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS

# List of files and folders to ignore to prevent glitchy behavior from many program's save routines
IGNORE_LIST = ['_tmp', '.git', '.tmp', '.TMP', '.crdownload']
# List of file extentions supported by the compilation handler
COMPILE_LIST = ['.xxxscss', '.coffee']
# The location of any CSS frameworks you wish to import to your .scss files via Sass imports.
SCSS_LOAD_PATHS = [
	'C:\\ruby187\\lib\\ruby\\gems\\1.8\\gems\\compass-0.12.2\\frameworks\\compass\\stylesheets\\',
	'C:\\ruby187\\lib\\ruby\\gems\\1.8\\gems\\compass-0.12.2\\frameworks\\blueprint\\stylesheets\\'
]

refresh = False


class BroadcastServerProtocol(WebSocketServerProtocol):

	def onOpen(self):
		self.factory.register(self)

	def onMessage(self, msg, binary):
		global settings
		if not binary:
			data = json.loads(msg)
			for key in data.iterkeys():
				if key == "handshake":
					if data[key][:len(settings['live_url'])] == settings['live_url']:
						self.factory.broadcast('{"handshake":"true"}')
					else:
						self.factory.broadcast('{"handshake":"false"}')
			return True

	def connectionLost(self, reason):
		WebSocketServerProtocol.connectionLost(self, reason)
		self.factory.unregister(self)


class BroadcastServerFactory(WebSocketServerFactory):
	"""
	Simple broadcast server broadcasting any message it receives to all
	currently connected clients.
	"""
	def __init__(self, url, debug = False, debugCodePaths = False):
		WebSocketServerFactory.__init__(self, url, debug = debug, debugCodePaths = debugCodePaths)
		self.clients = []
		self.tickcount = 0
		self.tick()

	def tick(self):
		global settings
		global refresh
		if refresh == True:
			self.broadcast('{"refresh": "' + settings['live_url'] + '"}')
			refresh = False

		self.tickcount += 1
		#self.broadcast("'refresh %d' from server" % self.tickcount)
		reactor.callLater(0.5, self.tick)

	def register(self, client):
		if not client in self.clients:
			#print console("Connected to web browser @ " + client.peerstr,  event = 'Message')
			self.clients.append(client)

	def unregister(self, client):
		if client in self.clients:
			#print "unregistered client " + client.peerstr
			self.clients.remove(client)

	def broadcast(self, msg):
		for c in self.clients:
			c.sendMessage(msg)
			#print "message sent to " + c.peerstr



def refresh_server():
	debug = False

	ServerFactory = BroadcastServerFactory
	#ServerFactory = BroadcastPreparedServerFactory

	factory = ServerFactory("ws://localhost:9000",
						   debug = debug,
						   debugCodePaths = debug)

	factory.protocol = BroadcastServerProtocol
	factory.setProtocolOptions(allowHixie76 = True)
	listenWS(factory)

	webdir = File(settings['local_path'])
	web = Site(webdir)
	reactor.listenTCP(8080, web)
	webbrowser.open(settings['live_url'])
	reactor.run()




def console(message,  event = 'Message', event_object = ''):

	now = datetime.datetime.now()
	print Style.DIM + Fore.WHITE + now.strftime("%I:%M.%S %p -") + Style.RESET_ALL,

	# Coloring
	output = Style.BRIGHT
	if event == 'Message' or event == 'Updated':
		output = output + Fore.YELLOW
	elif event == 'Created':
		output = output + Fore.GREEN
	elif event == 'Deleted' or event == 'Warning':
		output = output + Fore.RED
	elif event == 'Moved' or event == 'Compile':
		output = output + Fore.CYAN

	if str(event_object) != '':
		# Special formatting for certain events
		if event == 'Moved':
			old_path = win_to_lin_path(event_object.src_path)
			old_path = old_path[len(settings['remote_path'])+1:]
			new_path = win_to_lin_path(event_object.dest_path)
			new_path = new_path[len(settings['remote_path'])+1:]

			output = output + '  ' + event + Style.RESET_ALL + Fore.WHITE

			output = output + ": " + old_path + '\n' + '            -      ' + Fore.CYAN + Style.BRIGHT +'to'+ Fore.WHITE +': ' + new_path + Style.RESET_ALL
		else:
			remotepath = win_to_lin_path(event_object.src_path)
			remotepath = remotepath[len(settings['remote_path'])+1:]

			output = output + event + Style.RESET_ALL + Style.DIM + Fore.WHITE

			if message == '':
				output = output + ': ' + Style.BRIGHT + remotepath + Style.DIM
			else:
				output = output + ': ' + Style.BRIGHT + remotepath + Style.DIM + ' ' + message
	else:
		output = output + event + Style.RESET_ALL + Style.DIM + Fore.WHITE
		output = output + ': ' + Style.BRIGHT + message + Style.DIM

	return output


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

def get_filename(event):
	file_path = event.src_path
	file_path = file_path[len(settings['local_path'])+1:]
	path_elements = file_path.split('\\')
	file_name = path_elements[len(path_elements)-1]
	return file_name

def compile_file(compile_list, event):
	file_path = event.src_path
	file_name = get_filename(event)


	for file_extention in compile_list:
		if file_extention in file_path:
			if file_extention == '.scss':
				compile_scss(event)
			elif file_extention == '.coffee':
				compile_coffee(event)
			else:
				print console(file_extention + ' support coming soon...', 'Message', event)

			return 1
	return 0

def compile_scss(event):
	scss.LOAD_PATHS = SCSS_LOAD_PATHS
	_scss_vars = {}
	_scss = scss.Scss(
		scss_vars=_scss_vars,
		scss_opts={
			'compress': False,
			'debug_info': False,
		}
	)
	file_name = get_filename(event)

	scss_file = open(event.src_path, 'r').read()
	compiled_css = _scss.compile(scss_file)

	compiled_path = event.src_path[:-len(file_name)]
	compiled_file_name = file_name.split('.')
	compiled_file_name = compiled_file_name[0] + '.css'

	css_file = open(compiled_path + compiled_file_name, 'w')
	css_file.write(compiled_css)
	css_file.close()

	print console('', 'Compile', event)

def compile_coffee(event):
	file_name = get_filename(event)

	coffee_file = open(event.src_path, 'r').read()
	compiled_js = coffeescript.compile(coffee_file)

	compiled_path = event.src_path[:-len(file_name)]
	compiled_file_name = file_name.split('.')
	compiled_file_name = compiled_file_name[0] + '.js'

	css_file = open(compiled_path + compiled_file_name, 'w')
	css_file.write(compiled_js)
	css_file.close()


def ignore_file(ignore_list, event):
	"return 1 (true) if any of the ignore_list are in file_path"
	file_path = event.src_path
	file_path = file_path[len(settings['local_path'])+1:]
	path_elements = file_path.split('\\')
	file_name = path_elements[len(path_elements)-1]

	if file_path.find('\\') != -1:
		if len(path_elements[len(path_elements)-1]) <= 4:
			return 1

	# ignore weird linux file saving BS from certain apps (like gedit)
	
	if file_name[:1] == '.':
		return 1

	for file_name in ignore_list:
		if file_name in file_path:
			#print console('', 'Ignored', event)
			return 1
	return 0


def create_file(event, client, ssh):
	localpath = event.src_path
	remotepath = win_to_lin_path(localpath)

	# Wait some time before uploading the file because some 
	# apps do weird stuff to files as they're being saved.
	time.sleep(1.2)
	if local_file_exists(localpath):
		if not remote_file_exists(client, remotepath, ssh):
			if settings['port'] == 22:
				client.put(localpath, remotepath)
			else:
				client.upload(localpath, remotepath)

			sync_logger.info('Created File: %s', remotepath)
			print console('', 'Created', event)
		else:
			print console('remote file already exists', 'Warning', event)

def create_directory(event, client, ssh):
	new_directory = win_to_lin_path(event.src_path)

	if settings['port'] == 22:
		if remote_directory_exists(client, new_directory, ssh):
			print console('remote directory already exists', 'Warning', event)
		else:
			client.mkdir(new_directory)
			print console('', 'Created', event)
			sync_logger.info('Created Folder: %s', new_directory)
	else:
		client.mkdir(new_directory)
		print console('', 'Created', event)
		sync_logger.info('Created Folder (FTP): %s', new_directory)


def update_file(event, client, ssh):
	localpath = event.src_path
	remotepath = win_to_lin_path(event.src_path)

	if settings['port'] == 22:
		if local_file_exists(localpath):
			if sftp_is_file(ssh, remotepath):
				client.put(localpath, remotepath)
				print console('', 'Updated', event)
				sync_logger.info('Updated: %s', remotepath)
			else:
				print console('remote file not found', 'Warning', event)
				print console('attempting to create file', 'Message', event)
				create_file(event, client, ssh)
	else:
		if local_file_exists(localpath):
			client.upload(localpath, remotepath)
			print console('', 'Updated', event)
			sync_logger.info('Updated (FTP): %s', remotepath)


def move_file(event, client, ssh):
	old_path = win_to_lin_path(event.src_path)
	new_path = win_to_lin_path(event.dest_path)
	cmd  = 'mv "' + old_path + '" "' + new_path + '"'
	now = datetime.datetime.now()

	if settings['port'] == 22:
		if remote_file_exists(client, old_path, ssh):
			ssh.exec_command(cmd)
			print console('', 'Moved', event)
			sync_logger.info('Moved: %s', old_path)
			sync_logger.info('   to: %s', new_path)
		else:
			print console('remote file not found', 'Warning', event)


def move_directory(event, client, ssh):
	old_path = win_to_lin_path(event.src_path)
	new_path = win_to_lin_path(event.dest_path)
	cmd  = 'mv "' + old_path + '" "' + new_path + '"'

	if settings['port'] == 22:
		ssh.exec_command(cmd)
		sync_logger.info('Moved: %s', old_path)
		sync_logger.info('   to: %s', new_path)
		print console('', 'Moved', event)


def delete_file(event, client, ssh):
	old_file = win_to_lin_path(event.src_path)
	if settings['port'] == 22:
		if sftp_exists(client, old_file):
			ssh.exec_command('rm -r "' + old_file + '"')
			print console('', 'Deleted', event)
			sync_logger.info('Deleted File: %s', old_file)
		else:
			print console('folder or file does not exist', 'Warning', event)
			sync_logger.warning('Folder or file does not exist: %s', old_file)
	else:
		client.rmdir(old_file)
		print console('', 'Deleted', event)
		sync_logger.info('Deleted File (FTP): %s', old_file)


#class FileEventHandler(FileSystemEventHandler):
class FileEventHandler(FileSystemEventHandler):
	needs_refresh = False
	
	def __init__(self, ssh_client=None, ftp_client=None):
		if ssh_client is not None:
			self.ssh_client = ssh_client
			self.sftp_client = self.ssh_client.open_sftp()
		elif ftp_client:
			self.ftp_client = ftp_client

	def on_any_event(self, event):
		global refresh

		# Deleting
		if type(event) == watchdog.events.FileDeletedEvent:
			if not ignore_file(IGNORE_LIST, event):
				delete_file(event, self.sftp_client, self.ssh_client)
		elif type(event) == watchdog.events.DirDeletedEvent:
			#print 'DOESNT WORK ON WINDOWS SEE: https://github.com/gorakhargosh/watchdog/issues/92'
			if not ignore_file(IGNORE_LIST, event):
				delete_file(event, self.sftp_client, self.ssh_client)
		else:
			if not (ignore_file(IGNORE_LIST, event) or compile_file(COMPILE_LIST, event)):

				# Creating
				if type(event) == watchdog.events.FileCreatedEvent:
					create_file(event, self.sftp_client, self.ssh_client)
					refresh = True

				if type(event) == watchdog.events.DirCreatedEvent:
					create_directory(event, self.sftp_client, self.ssh_client)

				# Updating
				if type(event) == watchdog.events.FileModifiedEvent:
					update_file(event, self.sftp_client, self.ssh_client)
					refresh = True

				#if type(event) == watchdog.events.DirModifiedEvent:
					#print "DOESNT WORK ON WINDOWS SEE: https://github.com/gorakhargosh/watchdog/issues/92"  

				# Moving / Renaming
				if type(event) == watchdog.events.FileMovedEvent:
					move_file(event, self.sftp_client, self.ssh_client)
				if type(event) == watchdog.events.DirMovedEvent:
					move_directory(event, self.sftp_client, self.ssh_client)

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
	return False


def remote_file_exists(sftp, path, ssh):
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


def remote_directory_exists(sftp, path, ssh):
	cmd = 'test -d \''+path+'\' && echo "true" || echo "false"'
	stdin, stdout, stderr = ssh.exec_command(cmd)
	output = str(stdout.readlines())

	if 'false' in output:
		return False
	else:
		return True


def local_file_exists(PATH):
	if os.path.exists(PATH) and os.path.isfile(PATH) and os.access(PATH, os.R_OK):
		return True
	else:
		return False


""" 
-----------------------------------------------------------------------------------------------------------------------
- Application entry point for sync.py
-----------------------------------------------------------------------------------------------------------------------
"""
seperator = Fore.GREEN + Style.DIM + '-------------------------------------------------------------------------------' + Fore.WHITE + Style.BRIGHT

if __name__ == "__main__":

	# init colorama module
	color_init(autoreset=False)

	# Initialize python's logging facilities
	logging.basicConfig(format=' %(asctime)s %(levelname)s %(message)s')
	sync_logger = logging.getLogger(__name__)
	sync_logger.setLevel(logging.ERROR)

	# log SSH errors to file
	#paramiko.util.log_to_file('paramiko.log')
	#paramiko.util.logging.basicConfig(level=logging.ERROR)

	print seperator
	print Fore.WHITE + Style.BRIGHT + 'Welcome to ' + Fore.GREEN + Style.BRIGHT + 'sync.py' + Fore.WHITE + Style.BRIGHT

	# load external .config
	if local_file_exists('./sync.config'):
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
					print Fore.GREEN + Style.NORMAL + ' ' + str(i) + Fore.YELLOW + ' - ' + Fore.WHITE + Style.BRIGHT + project

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
					print Fore.RESET
					settings = load_config(project_list[project_select])
					print Fore.WHITE + Style.DIM + "Loading project: " + Style.BRIGHT + project_list[project_select]
			else:
				if len(project_list) >= 1:
					print Style.DIM + "Loading project: " + Style.BRIGHT + project_list[0]
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
				print Style.DIM + "Loading project: " + Style.BRIGHT + sys.argv[1]
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
			print Style.DIM + ' Local Folder: ' + Style.BRIGHT + settings['local_path']
			print Style.DIM + 'Remote Server: ' + Style.BRIGHT + 'ssh://' + settings['username'] + '@' + settings['host'] + ':' + str(settings['port'])
			print Style.DIM + 'Remote Folder: ' + Style.BRIGHT + settings['remote_path']
			event_handler = FileEventHandler(ssh_client=ssh_client)
			observer = Observer()
			observer.schedule(event_handler, settings['local_path'], recursive=True)
			observer.start()
			sync_logger.info('Watching ' + settings['local_path'])
			now = datetime.datetime.now()
			print "\n" + Fore.GREEN + "Now syncing" + Fore.WHITE + now.strftime(" - %m/%d/%Y %I:%M %p %Ss - ") + Fore.RED + Style.BRIGHT + "CTRL+C twice to exit."
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
			print now.strftime("\nNow syncing - %m/%d/%Y %I:%M %p %Ss - ") + Fore.RED + Style.BRIGHT + "CTRL+C to exit."
			print seperator

	refresh_server()
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