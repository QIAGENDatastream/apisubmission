#!/usr/bin/env python
import dsapi
import os, sys, argparse, json
import time
import pygments
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

def main(server):
    api = dsapi.DataStreamAPI(None, None, None)
    if api.is_endpoint_up():
        api.logger.info("Endpoint is up!")
        sys.exit(0)
    else:
        api.logger.critical("Endpoint looks down :(")
        sys.exit(1)

   
if __name__ == "__main__":
    parser = argparse.ArgumentParser("Check if Ingenuity endpoint is up", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--server', action="store", dest="server", default="https://api.ingenuity.com", help="url of server to construct URIs with")
    args = parser.parse_args()
    main(args.server)
