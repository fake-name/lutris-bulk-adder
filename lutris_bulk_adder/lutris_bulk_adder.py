#!/usr/bin/env python3

import re
import os
import sys
import hashlib
import sqlite3
import datetime
import traceback
import magic
import yaml


from . import constants


class GameYamlWrapper:
	def __init__(self):
		raise RuntimeError("Do not use this class directly")


	@staticmethod
	def linux_yaml(binary, working_dir):
		return {
			"game"  :  {
					"exe": binary,
					"working_dir": working_dir,
				},
			"system ": {},
			"linux"   : {},
		}

	@staticmethod
	def wine_yaml(binary, working_dir):
		return {
			"game"  :  {
					"exe": binary,
					"working_dir": working_dir,
				},
			"system ": {},
			"wine"   : {},
		}

	@staticmethod
	def mupen64_yaml(rom_file):
		return {
			"game": {
				"main_file": rom_file,
			},
			"mupen64plus": {},
			"system": {},
		}

	@staticmethod
	def mednafen_yaml(machine, rom_file):
		assert machine in [
				"gb",         # Game Boy (Color)
				"gba",        # Game Boy Advance
				"gg",         # Game Gear
				"md",         # Genesis/Mega Drive
				"lynx",       # Lynx
				"sms",        # Master System
				"gnp",        # Neo Geo Pocket (Color)
				"nes",        # NES
				"pce_fast",   # PC Engine
				"pcfx",       # PC-FX
				"psx",        # PlayStation
				"ss",         # Saturn
				"snes",       # SNES
				"wswan",      # WonderSwan
				"vb",         # Virtual Boy
		]

		return {
			"game": {
				"machine" : machine,
				"main_file": rom_file,
			},
			"mednafen": {},
			"system": {},
		}

	@staticmethod
	def snes9x_yaml(rom_file):
		'''
		I'm not entirely sure how this differes from mednafen in snes mode.
		'''
		return {
			"game": {
				"main_file": rom_file,
			},
			"snes9x": {},
			"system": {},
		}


class GameFileContainer:
	def __init__(self, path):

		dir_path, fname = os.path.split(path)
		fname, fext = os.path.splitext(fname)

		self._path      = path
		self._mime      = None
		self._name      = fname
		self._platform  = None
		self._runner    = None
		self._machine   = None
		self._yaml_ctnt = None


		fext = fext.lower()

		if fext in constants.NON_EXECUTABLE_EXTENSIONS:
			# print("Skipping", self._path)
			pass
		elif fext in constants.DEFAULT_ROM_FILE_EXTS:
			self.__id_from_ext(fext)
		else:
			self.__id_from_mime(dir_path)


	def __id_from_ext(self, ext):
		if ext in constants.SNES_EXT:
			self._platform = "Nintendo SNES"
			self._runner   = 'snes9x'
			self._yaml_ctnt = GameYamlWrapper.snes9x_yaml(self._path)

		elif ext in constants.N64_EXT:
			self._platform = "Nintendo 64"
			self._runner   = 'mupen64plus'
			self._yaml_ctnt = GameYamlWrapper.mupen64_yaml(self._path)

		elif ext in constants.GBA_EXT:
			self._platform = "Nintendo Game Boy Advance"
			self._runner   = 'mednafen'
			self._machine  = 'gba'
			self._yaml_ctnt = GameYamlWrapper.mednafen_yaml(self._machine, self._path)

		else:
			raise RuntimeError("Bad extension")

	def __id_from_mime(self, dir_path):
		self._mime = magic.from_file(self._path)

		if any([self._mime.startswith(tmp) for tmp in constants.IGNORE_TYPES]):
			return

		elif any([self._path.lower().endswith(tmp) for tmp in constants.IGNORE_BINARIES]):
			return

		elif any([self._path.lower().endswith(tmp + ".exe") for tmp in constants.IGNORE_BINARIES]):
			return

		elif any([self._mime.startswith(tmp) for tmp in constants.LINUX_EXECUTABLES + constants.SHELL_SCRIPTS]):
			self._platform = "Linux"
			self._runner = "linux"
			self._yaml_ctnt = GameYamlWrapper.linux_yaml(self._path, dir_path)

		elif any([self._mime.startswith(tmp) for tmp in constants.WINDOWS_EXECUTABLES]):
			self._platform = "Windows"
			self._runner = "wine"

			# Handle annoying rpgmaker games, which output their
			# projects with the main binary being "Game.exe", with
			# no additional metadata in the exe or anything.
			# As such, if the binary looks like that, use the folder name.
			if self._name.lower() == "game":
				_, dir_name = os.path.split(dir_path)
				self._name = dir_name

			self._yaml_ctnt = GameYamlWrapper.wine_yaml(self._path, dir_path)

		else:
			self._platform = "Unknown"
			self._runner = "unknown"

		# To handle: "DOS executable (COM)"

	def ok(self):

		if self._path is None:
			return False
		if self._platform is None:
			return False
		if self._runner is None:
			return False

		return True

	def get_platform(self):
		return self._platform

	def get_runner(self):
		return self._runner

	def get_binary_path(self):
		return self._path

	def get_yaml_contents(self):
		return self._yaml_ctnt

	def get_game_name(self):
		return self._name


def scan_for_supported_files(fdir, files=None):
	if files is None:
		files = set()


	with os.scandir(fdir) as it:
		for entity in it:
			if entity.is_file():
				entity_path = os.path.join(fdir, entity.name)

				# if not entity.name.lower().endswith(".exe"):
				# 	continue

				if any([entity.name.lower().endswith(tmp + ".exe") for tmp in constants.IGNORE_BINARIES]):
					continue

				fileid = GameFileContainer(entity_path)

				if not fileid.get_platform():
					continue

				# print((fileid._name, fileid._mime, entity_path))

				files.add(fileid)

			if entity.is_dir():
				dirp = os.path.join(fdir, entity.name)
				files |= scan_for_supported_files(dirp)
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

	# @classmethod
	# def from_file(cls, target_file, cursor, yaml_dir):
	# 	wrapper = GameFileContainer(target_file)

	def get_binary_path(self):
		if self.yaml_ctnt is None:
			return None
		if 'game' in self.yaml_ctnt:
			if 'exe' in self.yaml_ctnt['game']:
				game_key = 'exe'
			if 'main_file' in self.yaml_ctnt['game']:
				game_key = 'main_file'

			return self.yaml_ctnt['game'][game_key]

		return None


	def ok(self):
		if self.yaml_file is None or self.yaml_ctnt is None:
			return False

		# If the game has an executable, check it exists
		binary = self.get_binary_path()
		if binary is not None:
			if not os.path.exists(binary):
				print("Game binary does not exist: %s" % (self.yaml_ctnt['game'][game_key], ))
				return False
		else:
			print("No game entry in yaml? What?")
		return True

	def delete_entry(self, cursor):

		if self.yaml_file is not None and os.path.exists(self.yaml_file):
			os.remove(self.yaml_file)

		cursor.execute("DELETE FROM games WHERE slug = ?;", (self.slug, ))
		cursor.execute("COMMIT;")

def load_existing_games(yaml_dir, db_path=None, dry_run=False):

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

			if dry_run:
				print("Should remove entry:", entry)
			else:
				print("Removing entry:", entry)
				with conn as con:
					cur = con.cursor()
					entry.delete_entry(cur)


	return db_entries

def merge_lists(db_list, found_binaries):

	known = set([game.get_binary_path() for game in db_list])

	new = [
		game
			for
		game
			in
		found_binaries
			if
		game.get_binary_path() not in known
	]

	return new

def add_new_games(games, yaml_dir, db_path, dry_run):


	conn = sqlite3.connect(db_path)

	cur = conn.cursor()

	try:
		cur.execute("select max(id) from games")
	except sqlite3.OperationalError:
		print("SQLite error, is {} a valid Lutris database?".format(db_path))
		sys.exit(1)

	game_id = cur.fetchone()[0] + 1

	for game in games:
		ts = int(datetime.datetime.utcnow().timestamp())


		slug = re.sub(r"[^0-9A-Za-z']", " ", game.get_game_name())          # Split on nonword characters
		slug = slug.replace("'", "")                        # Strip apostrophe
		slug = re.sub(r"\s+", "-", slug).strip("-").lower() # Replace whitespace with dashes

		path_hash = hashlib.md5(game.get_binary_path().encode("utf-8")).hexdigest()
		config_file = '{slug}-{hash}'.format(slug=slug, hash=path_hash)
		slug = config_file
		config_file_path = os.path.join(yaml_dir, "{}.yml".format(config_file))



		db_values = {
			"id": game_id,
			"name": game.get_game_name(),
			"slug": slug,
			"installer_slug": None,
			"parent_slug": None,
			"platform": game.get_platform(),
			"runner": game.get_runner(),
			"executable": None,

			# I'm not sure what this is supposed to be used for
			"directory": os.path.join(os.path.expanduser('~'), 'Games'),

			"updated": None,
			"lastplayed": 0,
			"installed": 1,
			"installed_at": ts,
			"year": None,
			"configpath": config_file,
			"has_custom_banner": None,
			"has_custom_icon": None,
			"playtime": None,
			"hidden": 0,
			"service": None,
			"service_id": None
		}

		# Output to console
		if dry_run:
			print("file: {}".format(game.get_binary_path()))
			print("SQLite:\n{}".format(db_values))
			print("YML at {ymlfile}:\n{config}\n".format(
					ymlfile = config_file_path,
					config  = yaml.dump(game.get_yaml_contents(), default_flow_style=False))
				)

		# Write to DB/filesystem
		else:


			print("New game: '{slug}'".format(slug=db_values['slug']))

			print("Writing:", config_file_path)
			with open(config_file_path, 'w') as f:
				yaml.dump(game.get_yaml_contents(), f, default_flow_style=False)

			query = "INSERT INTO games ({columns}) VALUES ({placeholders})".format(
				columns = ','.join(db_values.keys()),
				placeholders = ','.join('?' * len(db_values))
			)

			cur.execute(query, list(db_values.values()))

			conn.commit()

		game_id += 1


def go(lutris_database,
		lutris_yaml_dir,
		directory,
		no_write,
		):

	print("Loading items from DB!")
	have = load_existing_games(yaml_dir=lutris_yaml_dir, db_path=lutris_database, dry_run=no_write)

	print("Scanning for games!")
	binaries = scan_for_supported_files(directory)
	print("Found %s potential games. Synchronizing." % (len(binaries), ))

	new_games = merge_lists(have, binaries)
	print("%s game entries are new." % (len(new_games), ))





	add_new_games(
			games    = new_games,
			db_path  = lutris_database,
			yaml_dir = lutris_yaml_dir,
			dry_run  = no_write
		)
	# print(have)



