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

import os, stat, errno

import fuse
from fuse import Fuse
fuse.fuse_python_api = (0, 2)

import apt
apt_cache = apt.Cache()

def bash(command):		
	return os.popen(command).read().split("\n")[:-1]

app_list = []
a = bash("dpkg --get-selections")#FIXME do in python!
for item in a:
    if not "deinstall" in item:
        app_list.append(item.split()[0])

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

def is_linked_path(path_list):
	if get_target_file_path(path_list) != False: #if get_taget comes up with any target, then it must be linked
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
		
def get_target_file_path(path_list):
	#assert is_linked_path(path_list)
	#programs, app_name, files, start of file path
	if len(path_list) >= 1 and path_list[0] == 'system':
		if len(path_list) >= 2 and path_list[1] == 'executables':
			if len(path_list) >= 3:
				#print translation['system']
				if path_list[2] in translation['system']['executables']: #ie quick
					return translation['system']['executables'][path_list[2]]
				else:	
					#######without tranlations#####	
					locations = [['bin'], ['sbin'], ['usr','bin'], ['usr','local','bin'], ['usr','sbin'], ['usr','local','sbin'], ['usr','games']]#[path_to_list(item) for item in os.getenv('PATH').split(":")]
					#ie like [['bin'], ['sbin'], ['usr','bin'], ['usr','local','bin'], ['usr','sbin'], ['usr','local','sbin'], ['usr','games']]#any more?
					for loc in locations:
						if len(path_list) >= 3 and path_list[2] in os.listdir(list_to_path(loc)):
							return loc+[path_list[2]]
		
	elif len(path_list) >= 1 and path_list[0] == 'programs':
		
		if len(path_list) >= 2: application = path_list[1]
		
		if len(path_list) >= 3 and path_list[2] == 'files':
			if len(path_list) >= 4: #ie any strictly sub folders 
				return path_list[3:]
		
		elif len(path_list) >= 3 and path_list[2] == application:#ie the executable file
			target = bash('which '+application)#find location of executable with same name as package
			assert target != []
			return path_to_list(target[0])
			
		elif len(path_list) >= 3 and path_list[2] == application+'.desktop':#ie the executable file
			return ['usr','share','applications',application+'.desktop']			
		
		elif len(path_list) >= 3 and path_list[2] == 'config':
			if len(path_list) == 4:#flat inside config
			
				if path_list[3] in translation['programs'][application]['config']: #quick
					return translation['programs'][application]['config'][path_list[3]]
				
				else: #slow #FIXME infact will soon not even produce the correct results #FIXME but if switch will need to call readdir if the keys arent there
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
	elif False:#other link paths
		None
	else:
		None
		#print "get_target_File_path .. shouldnt have got here"
	return False
	
		
def is_fake_file(path_list):
	if get_fake_file_contents(path_list) != False: #if get_fake_contents comes up with any content, then it must be fake
		#FIXME, when speed matters, dont actually bother going through the whole f get_fake_file_contents, ie run with args (path_list, "quick") and get it to stop
		return True	
#	#print path_list
#	if len(path_list) >= 1 and path_list[0] == 'programs':
#	#path[1] will be the program
#		if len(path_list) >= 3 and path_list[2] == 'desktop file': 
#			return True		
#	#else
#	return False

def get_fake_file_contents(path_list):
#	if len(path_list) >= 1 and path_list[0] == 'programs':
#	#path[1] will be the program
#		if len(path_list) >= 3 and path_list[2] == 'desktop file': 
#			return "hello"	
	#else
	return False

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
		
		files = []
		if len(path_list) == 0:
			files = ['programs', 'users', 'system', 'mount', 'libs']
		elif path_list[0] == 'programs':
		
			if not 'programs' in translation: translation['programs'] = {}
		
			if len(path_list) == 1:
				for item in app_list:
					if item[:3] != 'lib':
						files.append(item)
				#files = app_list
			else: #1 level down, inside program folder
				#inside program folders
				application = path_list[1]
				
				if not application in translation['programs']: translation['programs'][application] = {}
				
				if len(path_list) == 2:
					#top level folder stuff
					files = ['files', 'config', 'data']
					tmp = bash('which '+(path_list)[1])
					if not tmp == []:#ie this package has an associated executable
						files.append(application)
						
						found_launcher = False
						for item in os.listdir(list_to_path(['usr', 'share', 'applications'])):
							if item == application+'.desktop':
								found_launcher = True
								break
						if found_launcher == True:#as subet of programs will have launchers
							files.append(application+'.desktop')
				
				elif path_list[2] == 'files':
					installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
					for item in installed_files:
						std_item = path_to_list(item)
						if (['programs', application, 'files']+std_item)[:-1] == path_list:
							files.append(std_item[-1])
				
				elif path_list[2] == 'config':
				
					if not 'config' in translation['programs'][application]: translation['programs'][application]['config'] = {}
				
					assert len(path_list) <= 4 #just want flat config structure #FIXME files with the same name in different folders
					installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
					files = []
					for item in installed_files:
						std_item = path_to_list(item)
						if len(std_item) >= 1 and std_item[0] == 'etc':
							if len(std_item) >= 2:#dont want /etc itself
								if not os.path.isdir(list_to_path(std_item)):#or more... 
								
									translation['programs'][application]['config'][std_item[-1]] = std_item #FIXME needs to deal with mutliple items having same name
									#ie if this happen do name-(where_it_is_found)
								
									#for standardisation equivalent of: for item in translation['system']['executables']: files.append(translation['system']['executables'][item])
								
									files.append(std_item[-1])
									
									
				elif path_list[2] == 'data':
				
					if not 'data' in translation['programs'][application]: translation['programs'][application]['data'] = {}	
					
					assert len(path_list) <= 4
					installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
					files = []
					for item in installed_files:
						std_item = path_to_list(item)
						if len(std_item) > 1 and len(std_item[-1]) > 5:#crash checker
							if std_item[-1][-4:] in ['.png', '.jpg', '.mp3', '.wav', '.ico'] or std_item[-1][-5:] in ['.jpeg']:
								
								if not std_item[-1] in translation['programs'][application]['data']:#need recursive levels deep check FIXME
									translation['programs'][application]['data'][std_item[-1]] = std_item
									
								else:
									translation['programs'][application]['data'][std_item[-1]+'-('+std_item[-2]+')'] = std_item
							
								
								
								#old: files.append(std_item[-1])
					for item in translation['programs'][application]['data']:
						files.append(item)				
				else:
					print "readir else", path
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
					
					files += list_loc #FIXME or should write:
					#for standardisation: for item in translation['system']['executables']: files.append(translation['system']['executables'][item])
					
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
						
				
			#files = ['put something here']
		
		elif path_list[0] == '.Trash-1000':
			None	
		elif path_list[0] == '.Trash':
			None						
		else:
			#print "readir else", path
			files = ['this is a made up folder']
		
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
			
		
		elif False:
			#files created from nothing 
			None
		else:
			raise "error"
			
		#the main return that everything uses	
		slen = len(content)
		if offset < slen:
			if offset + size > slen:
				size = slen - offset
			buf = content[offset:offset+size]
		else:
			buf = ''
		return buf	

	#doenst work from here down
	
	def write(self, path, buf, offset, fh=None):
		path_list = path_to_list(path)
		"""
		Writes to the file.
		Returns the number of bytes written.
		"""
		if is_linked_path(path_list):
			f = open(get_target_file_path(path), 'r').read()
			content = f	
		
		
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
		
			#log(new_content)
		
			#f.close()
		
			g = open(get_target_file_path(path), 'w')
			g.write(new_content)
			g.close()
			return len(buf)
		elif False:
			None
			#files created from nothing 
		else:
			raise "error"		

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
