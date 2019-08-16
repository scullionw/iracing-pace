import argparse
import sys
from pathlib import Path
from iracing_web_api import iRacingClient, LoginFailed
from lapswarm import LapSwarm, EmptyResults, export_plot, interactive_plot
import credentials


def main(args):
    if args.reset:
        credentials.reset('iracing')

    user_pass = credentials.retrieve('iracing')
    if user_pass is None:
        username, password = credentials.query('iracing')
    else:
        username, password = user_pass
    
    try:
        iracing = iRacingClient(username, password)
    except LoginFailed:
        print("Login failed! Please check username and password.")
        sys.exit(1)
    else:
        credentials.persist('iracing', username, password)

    results = iracing.subsession_results(args.subsession)

    try:
        swarm = LapSwarm(results, args.maxpos, args.maxdelta)
    except EmptyResults:
        print("No subsession results, please check subsession ID.")
        sys.exit(1)

    title = args.title if args.title else args.subsession
    
    ax = swarm.create_plot(title, args.violin)
    
    if args.interactive:
        interactive_plot(ax)
    else:
        file_path = Path(f"{title}.png")
        export_plot(ax, file_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyse pace from iracing race session')

    parser.add_argument('subsession', type=str, help='Subsession ID')
    parser.add_argument('--maxpos', type=int, help='Minimum race position', default=5)
    parser.add_argument('--maxdelta', type=int, help='Maximum lap time delta to fastest lap', default=10)
    parser.add_argument('--violin', action='store_true', help='Use violin plot instead')
    parser.add_argument('--reset', action='store_true', help='Reset credentials')
    parser.add_argument('--interactive', action='store_true', help='Interactive graph instead of saving to file')
    parser.add_argument('--title', type=str, help='Title of race')

    sys.exit(main(parser.parse_args()))