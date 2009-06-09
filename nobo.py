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
	if len(path_list) >= 1 and path_list[0] == 'programs':
		if len(path_list) >= 3 and path_list[2] == 'files':
			return path_list[3:]
		elif len(path_list) >= 3 and path_list[2] == path_list[1]:
			target = bash('which '+path_list[1])#find location of executable with same name as package
			assert target != []
			return path_to_list(target[0])
		elif len(path_list) >= 3 and path_list[2] == 'config':
			if len(path_list) == 4:#flat inside config
				application = path_list[1]
				installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
				for item in installed_files:
					std_item = path_to_list(item)
					if len(std_item) >= 1 and std_item[0] == 'etc':#or more... 
						if len(std_item) >= 2: #dont want /etc itself
							if not os.path.isdir(list_to_path(std_item)):
								if std_item[-1] == path_list[-1]:
									return std_item#FIXME buggy if multiple with same name					
	elif len(path_list) >= 1 and path_list[0] == 'users':
		return ['home']+path_list[1:]#so just translates users into home
	elif len(path_list) >= 1 and path_list[0] == 'mount':
		return ['media']+path_list[1:]#so just translates users into home
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
	if len(path_list) >= 1 and path_list[0] == 'programs':
	#path[1] will be the program
		if len(path_list) >= 3 and path_list[2] == 'desktop file': 
			return "hello"	
	#else
	return False

def list_to_path(path_list):
	string = ''
	for item in path_list:#FIXME what about if no items, shoud it return '/'
		string = string+'/'+item
	return string

def path_to_list(path):
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
		#log("path "+path)
		st = MyStat()
		if is_linked_path(path_to_list(path)):
			target = get_target_file_path(path_to_list(path))
			st = os.stat(list_to_path(target))
		elif is_fake_file(path_to_list(path)):
			st.st_mode = stat.S_IFREG | 0755
			st.st_nlink = 1#FIXME does this need to be 1?
			st.st_uid = os.getuid()
			st.st_gid = os.getuid()
			st.st_size = len(get_fake_file_contents(path_to_list(path)))#len(whatever it is)
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
		files = []
		if len(path_to_list(path)) == 0:
			files = ['programs', 'users', 'system', 'mount', 'libs']
		elif path_to_list(path)[0] == 'programs':
			if len(path_to_list(path)) == 1:
				for item in app_list:
					if item[:3] != 'lib':
						files.append(item)
				#files = app_list
			else: #1 level down, inside program folder
				#inside program folders
				application = path_to_list(path)[1]
				if len(path_to_list(path)) == 2:
					#top level folder stuff
					files = ['files', 'config', 'data']
					tmp = bash('which '+(path_to_list(path))[1])
					if not tmp == []:#ie this package has an associated executable
						files += [path_to_list(path)[1], 'desktop file']
				elif path_to_list(path)[2] == 'files':
					installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
					#bash("dpkg -L "+application) 
					#print installed_files
					files = []
					for item in installed_files:
						std_item = path_to_list(item)
						if (['programs', application, 'files']+std_item)[:-1] == path_to_list(path):
							files.append(std_item[-1])
				elif path_to_list(path)[2] == 'config':
					assert len(path_to_list(path)) <= 4 #just want flat config structure #FIXME files with the same name in different folders
					installed_files = (str(item) for item in apt_cache[application].installedFiles)#should cache
					files = []
					for item in installed_files:
						std_item = path_to_list(item)
						if len(std_item) >= 1 and std_item[0] == 'etc':
							if len(std_item) >= 2:#dont want /etc itself
								if not os.path.isdir(list_to_path(std_item)):#or more... 
									files.append(std_item[-1])
				elif path_to_list(path)[2] == 'data':
					None				
				else:
					print "readir else", path
					raise "error"
					#shouldnt get to an else statement
					
		elif path_to_list(path)[0] == 'users':
			files = bash('ls /home'+list_to_path((path_to_list(path))[1:]))
		elif path_to_list(path)[0] == 'system':
			None
		elif path_to_list(path)[0] == 'mount':
			files = bash('ls /media'+list_to_path((path_to_list(path))[1:]))
			#files += bash('ls ~/.gvfs')#+list_to_path((path_to_list(path))[1:]))
		elif path_to_list(path)[0] == 'libs':
			for item in app_list:
				if item[:3] == 'lib':
					files.append(item)		
			files = ['put something here']
		
		elif path_to_list(path)[0] == '.Trash-1000':
			None	
		elif path_to_list(path)[0] == '.Trash':
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
		if False:#not path in app_list:
			return -errno.ENOENT
		if is_linked_path(path_to_list(path)):
			content = open(list_to_path(get_target_file_path(path_to_list(path))), 'rb').read()

		elif is_fake_file(path_to_list(path)):
			content = get_fake_file_contents(path_to_list(path))
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
		"""
		Writes to the file.
		Returns the number of bytes written.
		"""
		if is_linked_path(path_to_list(path)):
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
