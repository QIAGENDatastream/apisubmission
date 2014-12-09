import ingapi
import os, sys, argparse
import time

def main(endpoint, file_to_upload, log_level):
    api = ingapi.DataStreamAPI(endpoint, CLIENT_ID, CLIENT_SECRET, log_level=log_level)
    api.refresh_token()
    (resource_uri, err_msg) = api.submit_one_zipfile(file_to_upload)
    print api.get_package_status(resource_uri)



if __name__ == "__main__":
    (secret, client_id) = (None, None)
    if 'ING_CLIENT_SECRET' in os.environ:
        secret = os.environ['ING_CLIENT_SECRET']
    if 'ING_CLIENT_ID' in os.environ:
        client_id = os.environ['ING_CLIENT_ID']
    parser = argparse.ArgumentParser("Simple Script to Upload a zip file", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--server', action="store", dest="server", default="https://api-stable.ingenuity.com/datastream/api/v1/", help="url of upload endpoint")
    parser.add_argument('--pkg', action="store", dest="pkg", help="zip file of datafiles (VCF/ISA-TAB/XLS) to upload to ingenuity")
    parser.add_argument('--client-secret', action="store", default=secret, dest="secret", help="supply client secret on the command line, or set an environment variable named ING_CLIENT_SECRET")
    parser.add_argument('--client-id', action="store", default=client_id, dest="client_id", help="supply client id on the command, or set an environment variable named ING_CLIENT_ID")
    parser.add_argument('--logging-level', action="store", dest="log_level", default="WARNING", help="supplying debug will also start file logging for convenience")
    args = parser.parse_args()
    if not args.secret:
        parser.print_help()
        print >>sys.stderr, "\n\nPlease set the environment variable ING_CLIENT_SECRET \
                \nto be the client secret you find on the ingenuity developers \
                \nsite. You will also need to set ING_CLIENT_ID."
        sys.exit(1)
    else:
        CLIENT_SECRET=args.secret
    if not args.client_id:
        parser.print_help() 
        print >>sys.stderr, "\n\nPlease set the environment variable ING_CLIENT_ID\
                \nto be the client ID you find on the ingenuity developers site."
        sys.exit(1)
    else:
        CLIENT_ID=args.client_id
    if args.pkg==None or  not os.path.exists(args.pkg):
        parser.print_help()
        print >>sys.stderr, "\n\nERROR:Please supply a valid filename, %s does not appear to be a valid file" % args.pkg
        sys.exit(1)

    main(args.server, args.pkg, args.log_level)
