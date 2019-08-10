import argparse
import sys
from pathlib import Path
from iracing_pace.config import credentials
from iracing_web_api.iracing_web_api import iRacingClient
from iracing_pace.lapswarm import LapSwarm

def main(args):
    iracing = iRacingClient(credentials)
    results = iracing.subsession_results(args.subsession)

    swarm = LapSwarm(results, args.maxpos, args.maxdelta)

    title = args.title if args.title else args.subsession
    file_path = Path(f"{title}.png")

    swarm.export_plot(str(file_path), title, args.violin)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyse pace from iracing race session')

    parser.add_argument('subsession', type=str, help='Subsession ID')
    parser.add_argument('--maxpos', type=int, help='Minimum race position', default=5)
    parser.add_argument('--maxdelta', type=int, help='Maximum lap time delta to fastest lap', default=10)
    parser.add_argument('--violin', action='store_true', help='Use violin plot instead')
    parser.add_argument('--title', type=str, help='Title of race')

    sys.exit(main(parser.parse_args()))