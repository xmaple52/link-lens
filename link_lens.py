import argparse
import csv
import ipaddress
import math
import socket
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor


def validate_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise ValueError('Expected an HTTP(S) URL')
    if parts.username or parts.password:
        raise ValueError('URLs with credentials are not supported')
    for result in socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == 'https' else 80), type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(result[4][0]).is_global:
            raise ValueError('Only public internet addresses are supported')
    return url


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def check(url, timeout=10):
    try:
        validate_url(url)
        opener = build_opener(PublicRedirects())
        request = Request(url, method='HEAD', headers={'User-Agent': 'LinkLens/1.0'})
        try:
            response = opener.open(request, timeout=timeout)
        except HTTPError as error:
            if error.code not in (405, 501):
                raise
            request = Request(url, headers={'User-Agent': 'LinkLens/1.0', 'Range': 'bytes=0-0'})
            response = opener.open(request, timeout=timeout)
        with response:
            return (url, response.status, response.url, '')
    except HTTPError as error:
        error.close()
        return (url, error.code, error.url, str(error.reason))
    except (OSError, URLError, ValueError) as error:
        return (url, '', '', str(error))


def main():
    parser = argparse.ArgumentParser(description='Check public HTTP links, one URL per line.')
    parser.add_argument('file')
    parser.add_argument('--output', default='report.csv')
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2, metavar='1..4')
    parser.add_argument('--timeout', type=float, default=10)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be positive')
    try:
        with open(args.file, encoding='utf-8-sig') as stream:
            urls = list(dict.fromkeys(line.strip() for line in stream if line.strip() and not line.lstrip().startswith('#')))
        if len(urls) > 100:
            parser.error('Maximum 100 unique URLs per run')
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            rows = list(pool.map(lambda url: check(url, args.timeout), urls))
        with open(args.output, 'w', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['url', 'status', 'final_url', 'error'])
            writer.writerows(rows)
        for url, status, final_url, error in rows:
            print(f'{status or "ERROR"}  {url}')
        print(f'Saved {len(rows)} results to {args.output}')
        return int(any(not status or status >= 400 for _, status, _, _ in rows))
    except OSError as error:
        parser.exit(2, f'Error: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
