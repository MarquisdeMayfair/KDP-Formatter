#!/usr/bin/env python3
"""Build a local review draft using general or DirectorHelp configuration."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from publisher.build import PublishingConfig, build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--profile', choices=['general', 'directorhelp'], default='general')
    parser.add_argument('--mode', choices=['auto', 'preserve', 'reflow'], default='auto')
    parser.add_argument('--trim', default='6x9')
    parser.add_argument('--bleed', action='store_true')
    parser.add_argument('--bleed-strategy', choices=['validate', 'extend_edges'], default='validate')
    parser.add_argument('--print-cleanup', action='store_true')
    parser.add_argument('--first-page', type=int, default=1)
    parser.add_argument('--last-page', type=int)
    parser.add_argument('--format', choices=['pdf', 'epub', 'both'], default='pdf')
    args = parser.parse_args()
    try:
        report = build(args.input, args.output_dir, PublishingConfig(args.profile, args.mode, args.trim, args.bleed, args.first_page, args.last_page, args.format, args.bleed_strategy, args.print_cleanup))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Draft created: {args.output_dir}; profile={args.profile}, mode={report['resolved_mode']}")
    print('Local checks only; KDP acceptance and final approval remain outstanding.')
    return 1 if report.get('validation', {}).get('overall_status') == 'fail' else 0


if __name__ == '__main__':
    raise SystemExit(main())
