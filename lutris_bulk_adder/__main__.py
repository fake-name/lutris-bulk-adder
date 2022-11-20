#!/usr/bin/env python3

import re
import sys
import os.path
import argparse
import sqlite3

from .constants import DEFAULT_ROM_FILE_EXTS
from .constants import PLATFORMS
from .constants import IGNORE_TYPES
from .constants import IGNORE_BINARIES
from .constants import LINUX_EXECUTABLES
from .constants import WINDOWS_EXECUTABLES

from . import lutris_bulk_adder

def OptionListContainer(options):
	"""Option list type for argparse

	Args:
		options: String containing space-delimited key-value pairs in the form <name>=<value>

	Returns:
		dictionary containing parsed options

	Raises:
		argparse.ArgumentTypeError: Argument is formatted incorrectly
	"""

	pairs_raw = re.split(r"\s+", options)
	pairs = {}
	for pair in pairs_raw:
		parsed = pair.split('=', maxsplit=1)
		if len(parsed) < 2:
			raise argparse.ArgumentTypeError("Option \"{}\" is not formatted correctly".format(pair))

		pairs.update({parsed[0]: parsed[1]})

	return(pairs)


def DirectoryContainer(path):
	"""Directory type for argparse
	Args:
		path: directory path

	Returns:
		directory path
	Raises:
		argparse.ArgumentTypeError: Argument is not a directory
	"""
	if not os.path.isdir(path):
		raise argparse.ArgumentTypeError("{} is not a directory".format(path))
	else:
		return path


def main():
	parser = argparse.ArgumentParser(description='Scan a directory for ROMs to add to Lutris.')

	# Required arguments
	parser.add_argument('-d', '--directory', type=DirectoryContainer, required=True,
						help='Directory to scan for games.')

	# Lutris paths
	parser.add_argument('-ld', '--lutris-database', type=str,
						default=os.path.join(os.path.expanduser('~'), '.local', 'share', 'lutris', 'pga.db'),
						help='Path to the Lutris SQLite database.')
	parser.add_argument('-ly', '--lutris-yaml-dir', type=DirectoryContainer,
						default=os.path.join(os.path.expanduser('~'), '.config', 'lutris', 'games'),
						help='Directory containing Lutris yml files.')

	# parser.add_argument('-r', '--runner', type=str, required=True,
	# 					help='Name of Lutris runner to use.')
	# parser.add_argument('-p', '--platform', type=str, required=True, choices=PLATFORMS,
	# 					help='Platform name.')
	# parser.add_argument('-lg', '--lutris-game-dir', type=DirectoryContainer,
	# 					default=os.path.join(os.path.expanduser('~'), 'Games'),
	# 					help='Lutris games install dir.')
	# Other options
	# parser.add_argument('-f', '--file-types', type=str, nargs='*', default=DEFAULT_ROM_FILE_EXTS,
	# 					help='Space-separated list of file types to scan for.')
	# parser.add_argument('-o', '--game-options', type=OptionListContainer,
	# 					help='Additional options to write to the YAML file under the "game" key (e.g. platform number as required for Dolphin)')
	# parser.add_argument('-s', '--strip-filename', nargs='*', default=[],
	# 					help='Space-separated list of strings to strip from filenames when generating game names.')

	parser.add_argument('-n', '--no-write', action='store_true',
						help="""Do not write YML files or alter Lutris database, only print """
						"""data to be written out to stdout. (i.e. dry run)""")

	args = parser.parse_args()

	# Lutris SQLite db
	if os.path.isfile(args.lutris_database):
		conn = sqlite3.connect(args.lutris_database)
	else:
		print("Error opening database {}".format(args.lutris_database))
		sys.exit(1)

	lutris_database = args.lutris_database
	lutris_yaml_dir = args.lutris_yaml_dir
	directory       = args.directory
	# file_types      = args.file_types
	# strip_filename  = args.strip_filename
	# game_options    = args.game_options
	# lutris_game_dir = args.lutris_game_dir

	no_write        = args.no_write

	# platform        = args.platform
	# runner          = args.runner

	lutris_bulk_adder.go(lutris_database, lutris_yaml_dir, directory, no_write)


# def main():
# 	parser = argparse.ArgumentParser(description='Scan a directory for ROMs to add to Lutris.')

# 	# Required arguments
# 	parser.add_argument('-d', '--directory', type=DirectoryContainer, required=True,
# 						help='Directory to scan for games.')
# 	parser.add_argument('-r', '--runner', type=str, required=True,
# 						help='Name of Lutris runner to use.')
# 	parser.add_argument('-p', '--platform', type=str, required=True, choices=PLATFORMS,
# 						help='Platform name.')

# 	# Lutris paths
# 	parser.add_argument('-ld', '--lutris-database', type=str,
# 						default=os.path.join(os.path.expanduser('~'), '.local', 'share', 'lutris', 'pga.db'),
# 						help='Path to the Lutris SQLite database.')
# 	parser.add_argument('-ly', '--lutris-yml-dir', type=DirectoryContainer,
# 						default=os.path.join(os.path.expanduser('~'), '.config', 'lutris', 'games'),
# 						help='Directory containing Lutris yml files.')
# 	parser.add_argument('-lg', '--lutris-game-dir', type=DirectoryContainer,
# 						default=os.path.join(os.path.expanduser('~'), 'Games'),
# 						help='Lutris games install dir.')

# 	# Other options
# 	parser.add_argument('-f', '--file-types', type=str, nargs='*', default=DEFAULT_ROM_FILE_EXTS,
# 						help='Space-separated list of file types to scan for.')
# 	parser.add_argument('-o', '--game-options', type=OptionListContainer,
# 						help='Additional options to write to the YAML file under the "game" key (e.g. platform number as required for Dolphin)')
# 	parser.add_argument('-s', '--strip-filename', nargs='*', default=[],
# 						help='Space-separated list of strings to strip from filenames when generating game names.')
# 	parser.add_argument('-n', '--no-write', action='store_true',
# 						help="""
# Do not write YML files or alter Lutris database, only print data to be written out to stdout. (i.e. dry run)
# 	""")

# 	args = parser.parse_args()

# 	# Lutris SQLite db
# 	if os.path.isfile(args.lutris_database):
# 		conn = sqlite3.connect(args.lutris_database)
# 		cur = conn.cursor()
# 	else:
# 		print("Error opening database {}".format(args.lutris_database))
# 		sys.exit(1)

# 	# Get max game ID to increment from
# 	try:
# 		cur.execute("select max(id) from games")
# 	except sqlite3.OperationalError:
# 		print("SQLite error, is {} a valid Lutris database?".format(args.lutris_database))
# 		sys.exit(1)

# 	game_id = cur.fetchone()[0]
# 	if game_id is None:
# 		game_id = 0

# 	game_id = game_id + 1

# 	file_types = args.file_types

# 	if args.platform== "Windows":
# 		file_types = ['exe']

# 	# Scan dir for ROMs
# 	files = scan_for_supported_files(args.directory, args.file_types)

# 	for game_file in files:

# 		ts = int(datetime.utcnow().timestamp())

# 		# Generate game name and slug from filename
# 		game = re.sub(r"\..*", "", os.path.basename(game_file))  # Strip extension
# 		for token in args.strip_filename:
# 			game = game.replace(token, "")                  # Strip tokens
# 		game = re.sub(r"\s+", " ", game).strip(" ")         # Remove excess whitespace


# 		if args.platform== "Windows":
# 			dirp = os.path.split(game_file)[0]

# 			alt_name = os.path.split(dirp)[-1]
# 			if game == "Game":
# 				game = alt_name

# 		slug = re.sub(r"[^0-9A-Za-z']", " ", game)          # Split on nonword characters
# 		slug = slug.replace("'", "")                        # Strip apostrophe
# 		slug = re.sub(r"\s+", "-", slug).strip("-").lower() # Replace whitespace with dashes

# 		# Data for YML file
# 		# config_file = '{slug}-{ts}'.format(slug=slug, ts=ts)
# 		path_hash = hashlib.md5(game_file.encode("utf-8")).hexdigest()
# 		config_file = '{slug}-{hash}'.format(slug=slug, hash=path_hash)
# 		slug = config_file
# 		config_file_path = os.path.join(args.lutris_yaml_dir, "{}.yml".format(config_file))

# 		if args.platform== "Windows":


# 			bad = set([
# 				"ffmpeg",
# 				"zsyncmake",
# 				"zsync",
# 				"UnityCrashHandler64",
# 				"UnityCrashHandler32",
# 				"python",
# 				"pythonw",
# 				"notification_helper",
# 				"dxwebsetup",
# 				"jjs",
# 				"javacpl",
# 				"java-rmi",
# 				"unins000",
# 				"Uninstaller",
# 				"Config",
# 				"unpack200",
# 				"ResetConfig",
# 				"CLaunchUS",
# 				"servertool",
# 				"orbd",
# 				"nwjc",
# 				"policytool",
# 				"rmiregistry",
# 				"cwebp",
# 				"UEPrereqSetup_x64",
# 				"tnameserv",
# 				"Launcher",
# 				"subprocess",
# 				"ktab",
# 				"klist",
# 				"kinit",
# 				"jp2launcher",
# 				"jabswitch",
# 				"pysemver",
# 				"payload",
# 				"rmid",
# 				"java",
# 				"javaw",
# 				"javaws",
# 				"OpenSaveFolder",
# 				])

# 			if game in bad:
# 				continue

# 			config = {
# 				args.runner: {},
# 				"game": {
# 					"exe"         : game_file,
# 					"working_dir" : dirp,
# 				},
# 				"system": {}
# 			}
# 		else:
# 			config = {
# 				args.runner: {},
# 				"game": {
# 					"main_file": game_file
# 				},
# 				"system": {}
# 			}

# 		if args.game_options is not None:
# 			config['game'].update(args.game_options)

# 		# Data for Lutris DB
# 		values = {
# 			"id": game_id,
# 			"name": game,
# 			"slug": slug,
# 			"installer_slug": None,
# 			"parent_slug": None,
# 			"platform": args.platform,
# 			"runner": args.runner,
# 			"executable": None,
# 			"directory": args.lutris_game_dir,
# 			"updated": None,
# 			"lastplayed": 0,
# 			"installed": 1,
# 			"installed_at": ts,
# 			"year": None,
# 			"configpath": config_file,
# 			"has_custom_banner": None,
# 			"has_custom_icon": None,
# 			"playtime": None,
# 			"hidden": 0,
# 			"service": None,
# 			"service_id": None
# 		}

# 		# Output to console
# 		if args.no_write:
# 			print("file: {}".format(game_file))
# 			print("SQLite:\n{}".format(values)),
# 			print("YML at {ymlfile}:\n{config}\n".format(ymlfile=config_file_path,
# 														 config=yaml.dump(config, default_flow_style=False)))

# 		# Write to DB/filesystem
# 		else:


# 			cur.execute("SELECT count(*) FROM games WHERE slug = ?", (values['slug'], ))
# 			have = cur.fetchone()[0]

# 			if not have:
# 				print("New game: '{slug}'".format(slug=values['slug']))

# 				print("Writing:", config_file_path)
# 				with open(config_file_path, 'w') as f:
# 					yaml.dump(config, f, default_flow_style=False)

# 				query = "INSERT INTO games ({columns}) VALUES ({placeholders})".format(
# 					columns = ','.join(values.keys()),
# 					placeholders = ','.join('?' * len(values))
# 				)

# 				cur.execute(query, list(values.values()))
# 			else:
# 				print("Already have:", values['slug'])

# 			conn.commit()

# 		game_id += 1


if __name__ == '__main__':
	main()
