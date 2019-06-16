import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-s","--show", help="Show video (Need GUI)", action="store_true")
parser.add_argument("-t","--testmode", help="Mode test (pas d'activation du relais)", action="store_true")
args = parser.parse_args()
if args.show:
    print("Mode video")
if args.testmode:
    print("Mode test")
if not args.testmode:
    print("Mode real")
