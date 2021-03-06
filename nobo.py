#	Nobo is an implementation of a sensible linux filesystem structure written in fuse
#
#	Copyright (C) 2009  Duncan Hawthorne
#
#	This program is free software; you can redistribute it and/or
#	modify it under the terms of the GNU General Public License
#	as published by the Free Software Foundation; either version 2
#	of the License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program; if not, write to the Free Software
#	Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys

#print sys.argv
if __name__ == '__main__':
	mount_point = sys.argv[2]
else:	
	#FIXME deal with interactive
	print "have not dealt with mount point when run from interactive python session"

import os, stat, errno

import fuse
from fuse import Fuse
fuse.fuse_python_api = (0, 2)

import apt
apt_cache = apt.Cache()

import gtk
GTK = gtk.IconTheme()
GTK.set_custom_theme('Mac4Lin_Icons')#FIXME set current theme

package_provider_dict = {}

def bash(command):		
	return os.popen(command).read().split("\n")[:-1]

def list_to_path(path_list):
	#converts ['usr','bin','gedit'] to '/usr/bin/gedit'
	string = ''
	for item in path_list:#FIXME what about if no items, shoud it return '/'
		string = string+'/'+item
	return string

def path_to_list(path):
	#converts '/usr/bin/gedit' to ['usr','bin','gedit']
	first = path.split("/")
	if len(first) == 0:
		return first
	if first[0] == '':
		first = first[1:]
	if len(first) == 0:
		return first		
	if first[-1] == '':
		first = first[:-1]
	return first


app_list = []
a = bash("dpkg --get-selections")#FIXME do in python!
for item in a:
    if not "deinstall" in item:
        app_list.append(item.split()[0])

#app_list = app_list[:100]

gui_apps = [] #front facing applications. apps with launchers
for file_name in os.listdir('/usr/share/applications'):
	gui_apps.append(file_name.split('.desktop')[0])

if __name__ == '__main__':		
	#custom icons #FIXME this needs nautilus to be killed and reopened to make this work
	#FIXME turn into a function, which automatically does it for everything in the folder, with folder.jpg (problem, wont be able to read the folder till this bit of code has already run, as we are reading our own fuse folder)
	if False: #FIXME return to True obviously
		icons_path = os.getenv('HOME')+'/.nautilus/metafiles/'+('file://'+mount_point+'/programs').replace('/', '%2F')+'.xml'
		#FIXME make work for paths containing spaces or other weird characters. need library function
		bash('touch '+icons_path)
		icons_file = open(icons_path, 'w')
		icons_text = '<?xml version="1.0"?>\n<directory>'
		for app in gui_apps:
			icons_text += '<file name="'+app+'" custom_icon="'+'folder.jpg'+'"/>\n'
		icons_text += '</directory>\n'
		icons_file.write(icons_text)
		icons_file.close()	

	if False: #FIXME return to True obviously
		icons_path = os.getenv('HOME')+'/.nautilus/metafiles/'+('file://'+mount_point+'/apps').replace('/', '%2F')+'.xml'
		#FIXME make work for paths containing spaces or other weird characters. need library function
		bash('touch '+icons_path)
		icons_file = open(icons_path, 'w')
		icons_text = '<?xml version="1.0"?>\n<directory>'
		for app in gui_apps:
			icons_text += '<file name="'+app+'" custom_icon="'+'folder.jpg'+'"/>\n'
		icons_text += '</directory>\n'
		icons_file.write(icons_text)
		icons_file.close()



class MyStat(fuse.Stat):
	def __init__(self):
		self.st_mode = 0
		self.st_ino = 0
		self.st_dev = 0
		self.st_nlink = 0
		self.st_uid = 0
		self.st_gid = 0
		self.st_size = 0
		self.st_atime = 0
		self.st_mtime = 0
		self.st_ctime = 0

		"""
		- st_mode (protection bits)
		- st_ino (inode number)
		- st_dev (device)
		- st_nlink (number of hard links)
		- st_uid (user ID of owner)
		- st_gid (group ID of owner)
		- st_size (size of file, in bytes)
		- st_atime (time of most recent access)
		- st_mtime (time of most recent content modification)
		- st_ctime (platform dependent; time of most recent metadata change on Unix,
				     or the time of creation on Windows).
		"""

translation = {}
#a dict list linked_file:location_of_thing_linked_to

def providing_package_func(start_file): #FIXME quicker, less fallback to gedit
	if start_file in package_provider_dict:
		providing_package = package_provider_dict[start_file]
	else:	
		try:
			providing_package = bash('dpkg --search /usr/share/applications/'+start_file+'.desktop')[0].split(':')[0]
		except:
			print path_list
			providing_package = 'gedit'
		package_provider_dict[start_file] = providing_package

	providing_package = package_provider_dict[start_file]
	return providing_package


def is_linked_path(path_list):
	output = get_target_file_path(path_list)
	if output != False and output != None: #if get_taget comes up with any target, then it must be linked
		#FIXME, when speed matters, dont actually bother going through the whole f get_target_file_path, ie run with args (path_list, "quick") and get it to stop
		return True
#	#print("is linked",path_list)
#	if len(path_list) >= 1 and path_list[0] == 'programs':
#		if len(path_list) >= 3 and path_list[2] == 'files':
#			if len(path_list) >= 4:
#				return True
#		if len(path_list) >= 3 and path_list[2] == path_list[1]:
#			return True
#		if len(path_list) >= 3 and path_list[2] == 'config':
#			if len(path_list) == 4 and not (path_list[-1] == '.' or path_list[-1] == '..' or path_list[-1] == '.hidden'): #ie not /etc itself #FIXME why is .hidden even possible
#				return True			
#	elif len(path_list) >= 1 and path_list[0] == 'users':
#		if len(path_list) >= 2:
#			return True
#	elif len(path_list) >= 1 and path_list[0] == 'mount':
#		if len(path_list) >= 2:
#			return True
#	elif False:#other linked apps
#		None
#	else:
#		return False

def application_to_icons(application): #FIXME speed me up with a library
	if application in gui_apps:
		icon = GTK.lookup_icon(application, 24, 0)
		if icon == None: #so second attempt
			output = open('/usr/share/applications/'+application+'.desktop', 'r').read()
			for line in output.split('\n'):
				if 'Icon' in line:
					path = line.split('=')[1]
					break
			try:
				path#check if it has been set
			except:
				return None
			icon = GTK.lookup_icon(path, 24, 0)
		if icon == None:
			return None
		else:
			return path_to_list(icon.get_filename())
	#else
	return None
	
def desktop_to_executable(application):
	output = open('/usr/share/applications/'+application+'.desktop', 'r').read()
	for line in output.split('\n'):
		if 'Exec' in line:
			executable = line.split('=')[1].split(" ")[0]
			break
	return executable
	
		
def get_target_file_path(path_list):
	assert not "/" in path_list

	#assert is_linked_path(path_list)
	#programs, app_name, files, start of file path
	if len(path_list) >= 1 and path_list[0] == 'system':
		if len(path_list) >= 2 and path_list[1] == 'executables':
			if len(path_list) >= 3:
				return translation['system']['executables'][path_list[2]]
	elif len(path_list) >= 1 and path_list[0] == 'programs':
		if len(path_list) >= 2: application = path_list[1]
		
		if len(path_list) >= 3 and path_list[2] == 'files':
			if len(path_list) >= 4: #ie any strictly sub folders 
				return path_list[3:]
	
		elif len(path_list) >= 3 and path_list[2] == application:#ie the executable file
			target = bash('which '+application)#find location of executable with same name as package
			assert target != []
			if path_to_list(target[0]) != None:
				return path_to_list(target[0])
			else:
				return False
			
		elif len(path_list) >= 3 and path_list[2] == application+'.desktop':#ie the executable file
			return ['usr','share','applications',application+'.desktop']			

		elif len(path_list) >= 3 and path_list[2] == 'folder.jpg':#FIXME stop calling a png a jpg
			icon_path_list = application_to_icons(application)
			if icon_path_list == None:
				return False
			else:
				return icon_path_list
		
		elif len(path_list) >= 3 and path_list[2] == 'config':
			if len(path_list) == 4:#flat inside config
			
				if path_list[3] in translation['programs'][application]['config']: #quick
					return translation['programs'][application]['config'][path_list[3]]
				
				else: #slow #FIXME infact will soon not even produce the correct results #FIXME but if switch will need to call readdir if the keys arent there
					print "slow else"
					installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
					for item in installed_files:
						std_item = path_to_list(item)
						if len(std_item) >= 1 and std_item[0] == 'etc':#or more... 
							if len(std_item) >= 2: #dont want /etc itself
								if not os.path.isdir(list_to_path(std_item)):
									if std_item[-1] == path_list[-1]:
										return std_item #FIXME buggy if multiple with same name	
		
		elif len(path_list) >= 3 and path_list[2] == 'data':
		
			
			if len(path_list) == 4:#flat inside
				if path_list[3] in translation['programs'][application]['data']: #quick
					return translation['programs'][application]['data'][path_list[3]]
				else:			
					installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
					for item in installed_files:
						std_item = path_to_list(item)
						if len(std_item) > 1 and len(std_item[-1]) > 5:#crash checker
							if std_item[-1][-4:] in ['.png', '.jpg', '.mp3', '.wav', '.ico'] or std_item[-1][-5:] in ['.jpeg']:
								if std_item[-1] == path_list[-1]:
									return std_item #FIXME buggy if multiple with same name						
	elif len(path_list) >= 1 and path_list[0] == 'users':
		return ['home']+path_list[1:]#so just translates users into home
	elif len(path_list) >= 1 and path_list[0] == 'mount':
		return ['media']+path_list[1:]#so just translates users into home
	elif len(path_list) >= 1 and path_list[0] == 'libs':
		None
	elif len(path_list) >= 1 and path_list[0] == 'apps':
		if len(path_list) == 1:
			return None
		else:# len(path_list) >= 2:
			if len(path_list) == 2:
				return None
			else:
				if len(path_list) == 3 and path_list[2] == 'folder.jpg': #FIXME have to do this, as dont want to call slow reverse file package lookup loads of times all in one go
					application = path_list[1]
					return application_to_icons(application)
				if len(path_list) == 3 and ( path_list[2] == 'config' or path_list[2] == 'data' or path_list[2] == 'files' ):
					return None #as in just make folders
				if len(path_list) == 3 and path_list[2] == path_list[1]+'.desktop':
					return ['usr','share','applications',path_list[1]+'.desktop']
				
				if len(path_list) == 3 and path_list[2] == desktop_to_executable(path_list[1]):
					target = bash('which '+path_list[1])[0]#find location of executable with same name as package
					return path_to_list(target)
				
				elif len(path_list) >= 4:
				
					providing_package = providing_package_func(path_list[1])
					linked_to =  get_target_file_path(['programs', providing_package]+path_list[2:])
					return linked_to			
			
					##if len(path_list) >= 4 and path_list[2] == 'package':
					#	providing_package = package_provider_dict[path_list[1]]
					#	linked_to =  get_target_file_path(['programs', providing_package]+path_list[2:])
					#	return linked_to
				else:
					print path_list
					print 'there is no other option'
	elif False:#other link paths
		None
	else:
		None
	return False
	
		
def is_fake_file(path_list):
	if get_fake_file_contents(path_list) != False: #if get_fake_contents comes up with any content, then it must be fake
		#FIXME, when speed matters, dont actually bother going through the whole f get_fake_file_contents, ie run with args (path_list, "quick") and get it to stop
		return True	

def get_fake_file_contents(path_list):
	if len(path_list) >= 1 and path_list[0] == 'programs':
		if len(path_list) >= 2 and path_list[1] == '.hidden':
			text = ''
			for application in app_list:#[:20]:#FIXME remove 20 restriction
				if not application in gui_apps:
					text += application+'\n'
			return text
	return False

def is_symlink(path_list):
	output = symlink_target(path_list)
	if output != None and output != False:
		return True
	#else
	return False	

def symlink_target(path_list):
	None


def related_packages(package):
	#FIXME extend to use actual debian dependencies, specifically packages 1 level up or down in dependencies?
	
	related = []
	
	for app in app_list:
		if app != package:#FIXME should this be left in
			if app[:len(package)] == package or (app[:3] == 'lib' and app[3:len(package) + 3] == package):
				related.append(app)
	return related


def directory_contents(path_list):
	files = []
	if len(path_list) == 0:
		files = ['programs', 'users', 'system', 'mount', 'libs', 'apps']
	elif path_list[0] == 'apps':
		if len(path_list) == 1:
			listed_dir = os.listdir('/usr/share/applications')
			for item in listed_dir:
				if item[-8:] == '.desktop':
					name = item.split('.desktop')[0]
					if '-' in name and name.split('-')[0]+'.desktop' in listed_dir: #try to cut out junk like apps like brasero-nautilus, just want brasero
						continue #ie
					else:
						files.append(name)
			#files = list(app.split('.')[0] for app in os.listdir('/usr/share/applications'))
		else:
			if len(path_list) == 2:
				files = ['folder.jpg', 'files','config','data',path_list[1]+'.desktop', desktop_to_executable(path_list[1])]
				None
			else:
				None
				if path_list[1] != '.hidden':#FIXME remove
					providing_package = providing_package_func(path_list[1])
					files = directory_contents(['programs', providing_package]+path_list[2:])
		
	elif path_list[0] == 'programs':
	
		if not 'programs' in translation: translation['programs'] = {}
	
		if len(path_list) == 1:
			for item in app_list:
				if item[:3] != 'lib':#FIXME probably remove
					files.append(item)
			
			files.append('.hidden') #FIXME perhaps remove this idea as now done better in 'apps'
			#files = app_list
		else: #1 level down, inside program folder
			#inside program folders
			application = path_list[1]
			
			if not application in translation['programs']: translation['programs'][application] = {}
			
			if len(path_list) == 2:
				#top level folder stuff
				files = ['files', 'config', 'data', 'folder.jpg']#FIXME remove folder.jpg
				tmp = bash('which '+(path_list)[1])
				if not tmp == []:#ie this package has an associated executable
					files.append(application)
					
					#as subet of programs will have launchers
					if application in gui_apps: 
						files.append(application+'.desktop')
			
			elif path_list[2] == 'files':
				
				for related_app in [application]+related_packages(application):
					installed_files = (str(item) for item in apt_cache[related_app].installedFiles)#should cache
					for item in installed_files:
						std_item = path_to_list(item)
						if (['programs', application, 'files']+std_item)[:-1] == path_list:
							files.append(std_item[-1])
			
			elif path_list[2] == 'config':
			
				if not 'config' in translation['programs'][application]: translation['programs'][application]['config'] = {}
			
				assert len(path_list) <= 4 #just want flat config structure #FIXME files with the same name in different folders
				
				for related_app in [application]+related_packages(application):
					installed_files = (str(item) for item in apt_cache[related_app].installedFiles)#should cache
					for item in installed_files:
						std_item = path_to_list(item)
						if len(std_item) >= 1 and std_item[0] == 'etc':
							if len(std_item) >= 2:#dont want /etc itself
								if not os.path.isdir(list_to_path(std_item)):#or more... 
							
									if not std_item[-1] in translation['programs'][application]['config']:
										translation['programs'][application]['config'][std_item[-1]] = std_item 
									else:
										translation['programs'][application]['config'][std_item[-1]+'-('+std_item[-2]+')'] = std_item
								
				for item in translation['programs'][application]['config']:
					files.append(item)									
								
			elif path_list[2] == 'data':
			
				if not 'data' in translation['programs'][application]: translation['programs'][application]['data'] = {}	
				
				assert len(path_list) <= 4
				
				for related_app in [application]+related_packages(application):
					installed_files = (str(item) for item in apt_cache[related_app].installedFiles)#should cache
					files = []
					for item in installed_files:
						std_item = path_to_list(item)
						if len(std_item) > 1 and len(std_item[-1]) > 5:#crash checker
							if std_item[-1][-4:] in ['.png', '.jpg', '.mp3', '.wav', '.ico'] or std_item[-1][-5:] in ['.jpeg']:
							
								if not std_item[-1] in translation['programs'][application]['data']:#need recursive levels deep check FIXME
									translation['programs'][application]['data'][std_item[-1]] = std_item
								
								else:
									translation['programs'][application]['data'][std_item[-1]+'-('+std_item[-2]+')'] = std_item
						
				for item in translation['programs'][application]['data']:
					files.append(item)				
			else:
				print "readir else", path_list
				raise "error"
				#shouldnt get to an else statement
				
	elif path_list[0] == 'users':
		files = os.listdir(list_to_path(['home']+(path_list)[1:]))
					
	elif path_list[0] == 'system':
		
		if not 'system' in translation: translation['system'] = {}
	
		if len(path_list) == 1:
			files = ['environment', 'executables', 'headers', 'libraries', 'manuals', 'shared', 'tasks']
		elif path_list[1] == 'environment':
			None
		elif path_list[1] == 'executables':
		
			#SPEED
			if not 'executables' in translation['system']: translation['system']['executables'] = {}			
		
			locations = [['bin'], ['sbin'], ['usr','bin'], ['usr','local','bin'], ['usr','sbin'], ['usr','local','sbin'], ['usr','games']]#[path_to_list(item) for item in os.getenv('PATH').split(":")]
			#ie like [['bin'], ['sbin'], ['usr','bin'], ['usr','local','bin'], ['usr','sbin'], ['usr','local','sbin'], ['usr','games']]#any more?
			for loc in locations:
				list_loc = os.listdir(list_to_path(loc))

				#SPEED
				for item in list_loc:
					translation['system']['executables'][item] = loc+[item] #FIXME need to run cleanup, inevitable memory leak
			
			for item in translation['system']['executables']: files.append(item)
				
		elif path_list[1] == 'headers':
			None
		elif path_list[1] == 'libraries':
			locations = [['lib'], ['usr','lib'], ['var','lib']]#any more?
			for loc in locations:
				files += (os.listdir(list_to_path(loc)))
		elif path_list[1] == 'manuals':
			None								
		elif path_list[1] == 'shared':
			None							
		elif path_list[1] == 'tasks':
			None				
	elif path_list[0] == 'mount':
		files = files = os.listdir(list_to_path(['media']+(path_list)[1:]))
	elif path_list[0] == 'libs':
		if len(path_list) == 1:
			for item in app_list:
				if item[:3] == 'lib':
					files.append(item)
		else: #1 level down, inside program folder
			#inside program folders
			application = path_list[1]
			if len(path_list) == 2:
				files = ['same as programs here but for libs']						
					
	
	elif path_list[0] == '.Trash-1000':
		None	
	elif path_list[0] == '.Trash':
		None						
	else:
		#print "readir else", path
		files = ['this is a made up folder']
	return files	

class HelloFS(Fuse):


	def getattr(self, path):
		path_list = path_to_list(path)
		
		#log("path "+path)
		st = MyStat()
		if is_linked_path(path_list):
			target = get_target_file_path(path_list)
			st = os.stat(list_to_path(target))
		elif is_fake_file(path_list):
			st.st_mode = stat.S_IFREG | 0755
			st.st_nlink = 2
			st.st_uid = os.getuid()
			st.st_gid = os.getuid()
			st.st_size = len(get_fake_file_contents(path_list))#len(whatever it is)
		elif is_symlink(path_list):
			None
		
		elif False:
			None
			#pther options, like files i will create from nothing
						
		else: #default to it being a folder
			st.st_mode = stat.S_IFDIR | 0755
			st.st_nlink = 2
			st.st_uid = os.getuid()
			st.st_gid = os.getuid()					
				        			        			
		return st

	def readdir(self, path, offset):
		path_list = path_to_list(path)
		
		files = directory_contents(path_list)
		
		#the yield that everything uses
		for r in  ['.', '..'] + files:
			yield fuse.Direntry(r)
						
			
	def open(self, path, flags):
		return
	#	if False:#not path in app_list:
	#		return -errno.ENOENT
	#	accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
	#	if (flags & accmode) != os.O_RDONLY:
	#		return -errno.EACCES

	def read(self, path, size, offset):
		path_list = path_to_list(path)
		
		if False:#not path in app_list:
			return -errno.ENOENT
		
		if is_linked_path(path_list):
			#content = open(list_to_path(get_target_file_path(path_list)), 'rb').read()
			
			target = open(list_to_path(get_target_file_path(path_list)), 'rb')
			target.seek(offset)
			return target.read(size)
			

		elif is_fake_file(path_list):
			content = get_fake_file_contents(path_list)
			#need to work out the buffer thing
			
			#standard bit given text called content
			slen = len(content)
			if offset < slen:
				if offset + size > slen:
					size = slen - offset
				buf = content[offset:offset+size]
			else:
				buf = ''
			return buf			
		
		elif False:
			#files created from nothing 
			None
		else:
			raise "error"
				
	

	#doenst work from here down
	
	def write(self, path, buf, offset, fh=None):
		path_list = path_to_list(path)
		"""
		Writes to the file.
		Returns the number of bytes written.
		"""
		if is_linked_path(path_list):
			#FIMXE must be a way to make this work like read, where you just write exactly into the part of the file that you want
			content = open(list_to_path(get_target_file_path(path_list)), 'r').read()
		
			if offset < len(content):
				# Write over part of the file. Save the bits we want to keep.
				before = content[:offset]
				after = content[offset+len(buf):]
			else:
				if offset > len(content):
					# First pad the file with 0s, using truncate
					content = content + '\0'*(size-len(content))
				before = content
				after = ''
			
			# Insert buf in between before and after
			new_content = before + buf + after		
		
		
			target = open(list_to_path(get_target_file_path(path_list)), 'w')
			target.seek(offset)
			target.write(new_content)
			target.close()
			return len(buf)

		elif is_fake_file(path_list):
			#FIXME non-functional
		
			if offset < len(content):
				# Write over part of the file. Save the bits we want to keep.
				before = content[:offset]
				after = content[offset+len(buf):]
			else:
				if offset > len(content):
					# First pad the file with 0s, using truncate
					content = content + '\0'*(size-len(content))
				before = content
				after = ''
			
			# Insert buf in between before and after
			new_content = before + buf + after			
			
			return len(buf)
			
			None
			#files created from nothing 
		else:
			raise "error"		
	
	def rmdir(self, path):
		path_list = path_to_list(path)
		if len(path_list) >= 1 and path_list[0] == 'programs':
			if len(path_list) == 2:
				print "uninstalling "+path_list[1]#FIXME actually do
		if len(path_list) >= 1 and path_list[0] == 'apps':
			if len(path_list) == 2:
				print "uninstalling "+providing_package_func(path_list[1])			
			else:
				return -errno.EOPNOTSUPP
		else:
			return -errno.EOPNOTSUPP
	
	def ftruncate(self, path, size, fh=None):
		return -errno.EOPNOTSUPP#
		
	def create(self, path, mode, rdev):
		return -errno.EOPNOTSUPP

	def fgetattr(self, path, fh=None):
		return -errno.EOPNOTSUPP

	def release(self, path, flags, fh=None):
		None

	def fsync(self, path, datasync, fh=None):
		None

	def flush(self, path, fh=None):	
		None
		
def main():
    usage="""
Userspace hello example

""" + Fuse.fusage
    server = HelloFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
