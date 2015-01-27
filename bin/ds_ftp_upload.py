#!/usr/bin/env python
import dsapi
import os, sys, argparse, json
import time
import pygments
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

def main(server, files_to_upload, log_level, ftp_dir):
    api = dsapi.DataStreamAPI(None, None, None, ftp_server=server,ftp_dir=ftp_dir)
    for file in files_to_upload:
        api.ftp_upload(file)



if __name__ == "__main__":
    (secret, client_id) = (None, None)
    parser = argparse.ArgumentParser("Simple Script to Upload files via FTP", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--server', action="store", dest="server", default="ftps2.ingenuity.com", help="url of FTP server to construct URIs with")
    parser.add_argument('--logging-level', action="store", dest="log_level", default="INFO", help="supplying debug will also start file logging for convenience")
    parser.add_argument('--upload-dir', action="store", dest="upload_dir", default=None, help="supply a directory to upload instead of files via the command lines")
    parser.add_argument('files', metavar='file1', nargs='+', help='a file to upload', )
    parser.add_argument('--ftp-dir', action="store", dest="ftp_dir", help="directory top upload to (should be in emailed instructions")
    args = parser.parse_args()
    if args.files==None:
        parser.print_help()
        print >>sys.stderr, "\n\nERROR:Please supply a valid filename, %s does not appear to be a valid file" % args.pkg
        sys.exit(1)
    main(args.server, args.files, args.log_level, args.ftp_dir)
