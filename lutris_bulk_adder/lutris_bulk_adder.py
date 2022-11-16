#!/usr/bin/env python3

import re
import os
import sys
import argparse
import hashlib
import magic
import yaml
import sqlite3
from datetime import datetime

DEFAULT_ROM_FILE_EXTS = ['iso', 'zip', 'sfc', 'gba', 'gbc', 'gb', 'md', 'n64',
                         'nes', '32x', 'gg', 'sms', 'bin', 'exe']
PLATFORMS = [
    '3DO',
    'Amstrad CPC',
    'Arcade',
    'Atari 2600',
    'Atari 7800',
    'Atari 800/5200',
    'Atari 8bit computers',
    'Atari Jaguar',
    'Atari Lynx',
    'Atari ST/STE/TT/Falcon',
    'Bandai WonderSwan',
    'ChaiLove',
    'Commodore 128',
    'Commodore 16/Plus/4',
    'Commodore 64',
    'Commodore VIC-20'
    'J2ME',
    'Magnavox Odyssey²',
    'MS-DOS',
    'MSX/MSX2/MSX2+',
    'NEC PC Engine (SuperGrafx)',
    'NEC PC Engine (TurboGrafx-16)',
    'NEC PC Engine TurboGrafx-16',
    'NEC PC-98',
    'NEC PC-FX',
    'Nintendo 3DS',
    'Nintendo DS',
    'Nintendo Game Boy (Color)',
    'Nintendo Game Boy Advance',
    'Nintendo Game Boy Color',
    'Nintendo GameCube',
    'Nintendo N64',
    'Nintendo NES',
    'Nintendo SNES',
    'Nintendo Virtual Boy',
    'Nintendo Wii',
    'Nintendo Wii/Gamecube',
    'Sega Dreamcast',
    'Sega Game Gear',
    'Sega Genesis',
    'Sega Genesis/Mega Drive',
    'Sega Maste System/Gamegear',
    'Sega Master System',
    'Sega Saturn',
    'Sharp X68000',
    'Sinclair ZX Spectrum',
    'Sinclair ZX81',
    'SNK Neo Geo Pocket (Color)',
    'SNK Neo Geo Pocket',
    'Sony PlayStation 2',
    'Sony PlayStation 3',
    'Sony PlayStation Portable',
    'Sony PlayStation',
    'Uzebox',
    'Vectrex',
    'Windows',
    'Z-Machine'
]

def option_list(options):
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


def directory(path):
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


IGNORE_TYPES = [
        "7-zip archive data",
        "Algol 68 source",
        "Applesoft BASIC program data",
        "color profile 2.0",
        "Crunch compressed texture",
        "DOS batch file",
        "DOS executable (block device driver)",
        "DOS/MBR boot sector",
        "executable",
        "FLAC audio bitstream data",
        "IFF data",
        "InnoSetup Log",
        "Intel ia64 COFF object file",
        "ISO Media",
        "ISO-8859 text ",
        "ISO-8859 text",
        "Java archive data (JAR)",
        "Java KeyStore",
        "Mach-O 64-bit x86_64 bundle",
        "Mach-O 64-bit x86_64 dynamically linked shared library",
        "Microsoft color profile 2.1",
        "MPEG sequence",
        "MS Windows 95 Internet shortcut text (URL=<http://www.rapapuru.com/>)",
        "MS Windows 95 Internet shortcut",
        "MS Windows icon resource - 11 icons",
        "MS Windows icon resource",
        "NekoVM bytecode",
        "Ogg data",
        "OpenPGP Public Key",
        "OpenType font data /run/media/mmcblk0p1/deck_sync/HG/GenderBender/renpy/common/fa5.otf",
        "OpenType font data",
        "Paint.NET image data",
        "PC bitmap ",
        "PC bitmap",
        "PDF document",
        "python 3.8 byte-compiled",
        "raw G3 (Group 3) FAX",
        "RIFF (big-endian) data",
        "RIFF (little-endian) data",
        "Spectrum .TAP data",
        "Standard MIDI data ",
        "Standard MIDI data",
        "Sun KCMS color profile 2.0",
        "SysEx File",
        "Targa image data",
        "TTComp archive data",
        "Unicode text",
        "Windows desktop.ini",
        'Adobe Photoshop Image',
        'Apple Desktop Services Store',
        'ASCII text',
        'Audio file with ID3 version ',
        'C source',
        'C source, ASCII text',
        'C++ source',
        'CSV text',
        'data',
        'DIY-Thermocam',
        'ELF 32-bit LSB shared object',
        'ELF 64-bit LSB shared object',
        'empty',
        'exported SGML document',
        'Generic INItialization configuration',
        'GIF image data',
        'GIMP XCF image data',
        'HTML document',
        'JPEG image data',
        'JSON data',
        'MPEG ADTS',
        'MS Windows 3.1 help',
        'MS Windows help file Content',
        'MS Windows shortcut',
        'Non-ISO extended-ASCII text',
        'Ogg data, Vorbis audio',
        'PC bitmap',
        'PDF document ',
        'PE32 executable (DLL)',
        'PE32+ executable (DLL)',
        'PEM certificate',
        'PEM RSA private key',
        'PNG image data',
        'POSIX shell script',
        'POSIX tar archive',
        'python 2.7 byte-compiled',
        'RAR archive data',
        'Ruby script',
        'SVG Scalable Vector Graphics image',
        'TrueType Font data,',
        'Web Open Font Format',
        'WebAssembly',
        'WebM',
        'Windows WIN.INI',
        'XML 1.0 document',
        'Zip archive data',
        'zlib compressed data',

        # Revisit?
        'Python script, ASCII text',
        'Python script text executable Python script',
        'Python script, Unicode text',

        # Is there a runner for mac binaries?
        "Mach-O 64-bit x86_64 executable",
        "Mach-O universal binary",
    ]



IGNORE_BINARIES = set([
    "ffmpeg",
    "zsyncmake",
    "zsync",
    "unitycrashhandler64",
    "unitycrashhandler32",
    "python",
    "pythonw",
    "notification_helper",
    "dxwebsetup",
    "jjs",
    "qgen",
    "pack200",
    "javacpl",
    "java.exe",
    "unins000",
    "ue4prereqsetup_x64",
    "uninstaller",
    "config",
    "unpack200",
    "resetconfig",
    "claunchus",
    "servertool",
    "orbd",
    "nwjc",
    "policytool",
    "rmiregistry",
    "cwebp",
    "ueprereqsetup_x64",
    "tnameserv",
    "launcher",
    "subprocess",
    "ktab",
    "klist",
    "kinit",
    "jp2launcher",
    "jabswitch",
    "pysemver",
    "payload",
    "rmid",
    "java",
    "vcredist-x64",
    "vcredist-x86",
    "vcredist_x64",
    "vcredist_x86",
    "javaw",
    "javaws",
    "opensavefolder",
    ])


LINUX_EXECUTABLES = [
    "ELF 32-bit LSB",
    "ELF 64-bit LSB",
]
WINDOWS_EXECUTABLES = [
    "PE32 executable",
    "PE32+ executable",
]

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


def scan_for_supported_files(fdir, types, files = None):
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

                # fileid = FileIdentifier(entity_path)
                # platform, runner = fileid.get_platform_runner()

                # if not platform:
                #     continue
                # print(fileid._mime, entity_path)

                if any([entity.name.lower().endswith(tmp + ".exe") for tmp in IGNORE_BINARIES]):
                    continue


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

def main():
    parser = argparse.ArgumentParser(description='Scan a directory for ROMs to add to Lutris.')

    # Required arguments
    parser.add_argument('-d', '--directory', type=directory, required=True,
                        help='Directory to scan for games.')
    parser.add_argument('-r', '--runner', type=str, required=True,
                        help='Name of Lutris runner to use.')
    parser.add_argument('-p', '--platform', type=str, required=True, choices=PLATFORMS,
                        help='Platform name.')

    # Lutris paths
    parser.add_argument('-ld', '--lutris-database', type=str,
                        default=os.path.join(os.path.expanduser('~'), '.local', 'share', 'lutris', 'pga.db'),
                        help='Path to the Lutris SQLite database.')
    parser.add_argument('-ly', '--lutris-yml-dir', type=directory,
                        default=os.path.join(os.path.expanduser('~'), '.config', 'lutris', 'games'),
                        help='Directory containing Lutris yml files.')
    parser.add_argument('-lg', '--lutris-game-dir', type=directory,
                        default=os.path.join(os.path.expanduser('~'), 'Games'),
                        help='Lutris games install dir.')

    # Other options
    parser.add_argument('-f', '--file-types', type=str, nargs='*', default=DEFAULT_ROM_FILE_EXTS,
                        help='Space-separated list of file types to scan for.')
    parser.add_argument('-o', '--game-options', type=option_list,
                        help='Additional options to write to the YAML file under the "game" key (e.g. platform number as required for Dolphin)')
    parser.add_argument('-s', '--strip-filename', nargs='*', default=[],
                        help='Space-separated list of strings to strip from filenames when generating game names.')
    parser.add_argument('-n', '--no-write', action='store_true',
                        help="""
Do not write YML files or alter Lutris database, only print data to be written out to stdout. (i.e. dry run)
    """)

    args = parser.parse_args()

    # Lutris SQLite db
    if os.path.isfile(args.lutris_database):
        conn = sqlite3.connect(args.lutris_database)
        cur = conn.cursor()
    else:
        print("Error opening database {}".format(args.lutris_database))
        sys.exit(1)

    # Get max game ID to increment from
    try:
        cur.execute("select max(id) from games")
    except sqlite3.OperationalError:
        print("SQLite error, is {} a valid Lutris database?".format(args.lutris_database))
        sys.exit(1)

    game_id = cur.fetchone()[0]
    if game_id is None:
        game_id = 0

    game_id = game_id + 1

    file_types = args.file_types

    if args.platform== "Windows":
        file_types = ['exe']

    # Scan dir for ROMs
    files = scan_for_supported_files(args.directory, args.file_types)

    for game_file in files:

        ts = int(datetime.utcnow().timestamp())

        # Generate game name and slug from filename
        game = re.sub(r"\..*", "", os.path.basename(game_file))  # Strip extension
        for token in args.strip_filename:
            game = game.replace(token, "")                  # Strip tokens
        game = re.sub(r"\s+", " ", game).strip(" ")         # Remove excess whitespace


        if args.platform== "Windows":
            dirp = os.path.split(game_file)[0]

            alt_name = os.path.split(dirp)[-1]
            if game == "Game":
                game = alt_name

        slug = re.sub(r"[^0-9A-Za-z']", " ", game)          # Split on nonword characters
        slug = slug.replace("'", "")                        # Strip apostrophe
        slug = re.sub(r"\s+", "-", slug).strip("-").lower() # Replace whitespace with dashes

        # Data for YML file
        # config_file = '{slug}-{ts}'.format(slug=slug, ts=ts)
        path_hash = hashlib.md5(game_file.encode("utf-8")).hexdigest()
        config_file = '{slug}-{hash}'.format(slug=slug, hash=path_hash)
        slug = config_file
        config_file_path = os.path.join(args.lutris_yml_dir, "{}.yml".format(config_file))

        if args.platform== "Windows":


            bad = set([
                "ffmpeg",
                "zsyncmake",
                "zsync",
                "UnityCrashHandler64",
                "UnityCrashHandler32",
                "python",
                "pythonw",
                "notification_helper",
                "dxwebsetup",
                "jjs",
                "javacpl",
                "java-rmi",
                "unins000",
                "Uninstaller",
                "Config",
                "unpack200",
                "ResetConfig",
                "CLaunchUS",
                "servertool",
                "orbd",
                "nwjc",
                "policytool",
                "rmiregistry",
                "cwebp",
                "UEPrereqSetup_x64",
                "tnameserv",
                "Launcher",
                "subprocess",
                "ktab",
                "klist",
                "kinit",
                "jp2launcher",
                "jabswitch",
                "pysemver",
                "payload",
                "rmid",
                "java",
                "javaw",
                "javaws",
                "OpenSaveFolder",
                ])

            if game in bad:
                continue

            config = {
                args.runner: {},
                "game": {
                    "exe"         : game_file,
                    "working_dir" : dirp,
                },
                "system": {}
            }
        else:
            config = {
                args.runner: {},
                "game": {
                    "main_file": game_file
                },
                "system": {}
            }

        if args.game_options is not None:
            config['game'].update(args.game_options)

        # Data for Lutris DB
        values = {
            "id": game_id,
            "name": game,
            "slug": slug,
            "installer_slug": None,
            "parent_slug": None,
            "platform": args.platform,
            "runner": args.runner,
            "executable": None,
            "directory": args.lutris_game_dir,
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
        if args.no_write:
            print("file: {}".format(game_file))
            print("SQLite:\n{}".format(values)),
            print("YML at {ymlfile}:\n{config}\n".format(ymlfile=config_file_path,
                                                         config=yaml.dump(config, default_flow_style=False)))

        # Write to DB/filesystem
        else:


            cur.execute("SELECT count(*) FROM games WHERE slug = ?", (values['slug'], ))
            have = cur.fetchone()[0]

            if not have:
                print("New game: '{slug}'".format(slug=values['slug']))

                print("Writing:", config_file_path)
                with open(config_file_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)

                query = "INSERT INTO games ({columns}) VALUES ({placeholders})".format(
                    columns = ','.join(values.keys()),
                    placeholders = ','.join('?' * len(values))
                )

                cur.execute(query, list(values.values()))
            else:
                print("Already have:", values['slug'])

            conn.commit()

        game_id += 1


if __name__ == '__main__':
    main()
