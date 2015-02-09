#!/usr/bin/env python
import dsapi
import os, sys, argparse, json
import time
import pygments
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

def main(server, files_to_upload, log_level, ftp_dir, finish, user, passwd):
    api = dsapi.DataStreamAPI(None, None, None, ftp_server=server,ftp_dir=ftp_dir, ftp_user=user, ftp_pass=passwd)
    for file in files_to_upload:
        api.ftp_upload(file)
    if(finish):
        finish_return = api.ftp_finish()
        print pygments.highlight(json.dumps(finish_return.json()),JsonLexer(),TerminalFormatter(bg="dark"))


if __name__ == "__main__":
    (secret, client_id) = (None, None)
    parser = argparse.ArgumentParser("Simple Script to Upload files via FTP", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--server', action="store", dest="server", default="ftps2.ingenuity.com", help="url of FTP server to construct URIs with")
    parser.add_argument('--logging-level', action="store", dest="log_level", default="INFO", help="supplying debug will also start file logging for convenience")
    parser.add_argument('--upload-dir', action="store", dest="upload_dir", default=None, help="supply a directory to upload instead of files via the command lines")
    parser.add_argument('--ftp-dir', action="store", dest="ftp_dir", help="directory top upload to (should be in emailed instructions")
    parser.add_argument('--finish', action="store_true", default=False, help="send 'package is done' signal at end of transfer")
    parser.add_argument('--username', action="store", dest="user", help="ingenuity username (email address you registered with", default=None)
    parser.add_argument('--password', action="store", dest="passwd", help="password for automated applications", default=None)
    parser.add_argument('files', metavar='file1', nargs='+', help='a file to upload', )
    args = parser.parse_args()
    if args.files==None:
        parser.print_help()
        print >>sys.stderr, "\n\nERROR:Please supply a valid filename, %s does not appear to be a valid file" % args.pkg
        sys.exit(1)
    print args.files
    main(args.server, args.files, args.log_level, args.ftp_dir, args.finish, args.user, args.passwd)
