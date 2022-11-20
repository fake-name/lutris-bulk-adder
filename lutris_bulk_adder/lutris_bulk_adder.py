#!/usr/bin/env python3

import re
import os
import sys
import hashlib
import sqlite3
import datetime
import magic
import traceback
import yaml


from .constants import DEFAULT_ROM_FILE_EXTS
from .constants import PLATFORMS
from .constants import IGNORE_TYPES
from .constants import IGNORE_BINARIES
from .constants import LINUX_EXECUTABLES
from .constants import WINDOWS_EXECUTABLES



class FileIdentifier:
	def __init__(self, path):
		self._path = path

		self._mime = magic.from_file(self._path)

		if any([self._mime.startswith(tmp) for tmp in IGNORE_TYPES]):
			self._platform = None
			self._runner   = None

		elif any([self._path.lower().endswith(tmp) for tmp in IGNORE_BINARIES]):
			self._platform = None
			self._runner   = None

		elif any([self._path.lower().endswith(tmp + ".exe") for tmp in IGNORE_BINARIES]):
			self._platform = None
			self._runner   = None

		elif any([self._mime.startswith(tmp) for tmp in LINUX_EXECUTABLES]):
			self._platform = "Linux"
			self._runner = "linux"

		elif any([self._mime.startswith(tmp) for tmp in WINDOWS_EXECUTABLES]):
			self._platform = "Windows"
			self._runner = "wine"
		else:
			self._platform = "Unknown"
			self._runner = "unknown"

		# To handle: "DOS executable (COM)"


	def get_platform_runner(self):
		return self._platform, self._runner


def scan_for_supported_files(fdir, types=None, files=None):
	"""Scans a directory for all files matching a list of extension types.

	Args:
		dir: Directory location to scan.
		types: List of file extensions to include.

	Returns:
		A list of file paths.

	Raises:
		FileNotFoundError: Directory does not exist.
	"""
	if files is None:
		files = set()


	with os.scandir(fdir) as it:
		for entity in it:
			if entity.is_file():
				entity_path = os.path.join(fdir, entity.name)

				if any([entity.name.lower().endswith(tmp + ".exe") for tmp in IGNORE_BINARIES]):
					continue

				if types is None:
					fileid = FileIdentifier(entity_path)
					platform, runner = fileid.get_platform_runner()

					if not platform:
					    continue
					print(fileid._mime, entity_path)

				else:
					fn_delimited = entity.name.split(os.extsep)
					try:
						if(fn_delimited[len(fn_delimited) - 1].lower() in types):
							files.add(entity_path)
					except IndexError:
						pass

			if entity.is_dir():
				dirp = os.path.join(fdir, entity.name)
				files |= scan_for_supported_files(dirp, types)
	return files

def load_yaml_file(yaml_file):
	assert os.path.isfile(yaml_file), "Yaml file (%s) does not exist, or is not a file!" % (yaml_file, )

	with open(yaml_file, "r") as fp:
		fctnt = yaml.safe_load(fp.read())
	return fctnt

class GameEntry:

	def __init__(self, name, slug, platform, runner, directory, installed_at, yaml_file):

		self.name         = name
		self.slug         = slug
		self.platform     = platform
		self.runner       = runner
		self.directory    = directory
		self.installed_at = installed_at

		self.yaml_file    = None
		self.yaml_ctnt    = None

		if os.path.exists(yaml_file):
			self.yaml_file = yaml_file
			self.yaml_ctnt = load_yaml_file(yaml_file)
		else:
			print("Yaml file (%s) for db row doesn't exist!" % (yaml_file, ))


	@classmethod
	def from_db_row(cls, row, yaml_file):
		instance = cls(
				name         = row['name'],
				slug         = row['slug'],
				platform     = row['platform'],
				runner       = row['runner'],
				directory    = row['directory'],
				installed_at = row['installed_at'],
				yaml_file     = yaml_file,
			)

		return instance

	@classmethod
	def from_file(cls, target_file, cursor, yaml_dir):
		pass


	def ok(self):
		if self.yaml_file is None or self.yaml_ctnt is None:
			return False

		# If the game has an executable, check it exists
		if 'game' in self.yaml_ctnt:
			if not os.path.exists(self.yaml_ctnt['game']['exe']):
				print("Game exe does not exist: %s" % (self.yaml_ctnt['game']['exe'], ))
				return False

		return True

	def delete_entry(self, cursor):

		if self.yaml_file is not None and os.path.exists(self.yaml_file):
			os.remove(self.yaml_file)

		cursor.execute("DELETE FROM games WHERE slug = ?;", (self.slug, ))
		cursor.execute("COMMIT;")

def load_existing_games(yaml_dir, db_path=None):

	# Lutris SQLite db
	if db_path is None:
		db_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'lutris', 'pga.db')

	assert os.path.isfile(db_path), "Database file (%s) does not seem to exist!" % (db_path, )
	assert os.path.isdir(yaml_dir), "Yaml directory (%s) does not exist, or is not a directory!" % (yaml_dir, )

	conn = sqlite3.connect(db_path)

	# Load db entries
	with conn as con:
		cur = con.cursor()

		cur.execute("SELECT name, slug, platform, runner, directory, installed_at, configpath FROM games;")
		res = cur.fetchall()

	db_entries = []

	for name, slug, platform, runner, directory, installed_at, configpath in res:
		row = {
			"name"         : name,
			"slug"         : slug,
			"platform"     : platform,
			"runner"       : runner,
			"directory"    : directory,
			"installed_at" : installed_at,
			"configpath"   : configpath
		}

		yaml_file = os.path.join(yaml_dir, configpath + ".yml")

		entry = GameEntry.from_db_row(row, yaml_file)
		if entry.ok():

			db_entries.append(entry)
		else:
			print("Should remove entry:", entry)

			with conn as con:
				cur = con.cursor()
				entry.delete_entry(cur)


	return db_entries


def go(lutris_database,
		# file_types,
		lutris_yaml_dir,
		# strip_filename,
		directory,
		# game_options,
		no_write,
		platform,
		runner,
		):

	print("Running!")
	have = load_existing_games(yaml_dir=lutris_yaml_dir, db_path=lutris_database)

	binaries = scan_for_supported_files(directory)

	# print(have)



