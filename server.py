#!/usr/bin/env python3
"""
Obsidian English - Local Development Server
Serves the web app and dynamically reads .md files from the articles folder.
"""

import http.server
import socketserver
import os
import json
from pathlib import Path
from urllib.parse import unquote

PORT = 8080
DIRECTORY = Path(__file__).parent.absolute()


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def do_GET(self):
        """Handle GET requests with special API endpoints"""
        path = unquote(self.path)

        # API endpoint: Get list of articles from articles folder
        if path == '/api/articles':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            articles = []
            articles_dir = DIRECTORY / 'articles'

            if articles_dir.exists():
                for md_file in sorted(articles_dir.glob('*.md')):
                    try:
                        content = md_file.read_text(encoding='utf-8')
                        # Extract title from first line (remove # prefix)
                        lines = content.strip().split('\n')
                        title = lines[0].lstrip('#').strip() if lines else md_file.stem

                        articles.append({
                            'title': title,
                            'filename': md_file.name,
                            'wordCount': len(content.split()),
                            'content': content
                        })
                    except Exception as e:
                        print(f"Error reading {md_file}: {e}")

            self.wfile.write(json.dumps(articles, ensure_ascii=False).encode('utf-8'))
            return

        # API endpoint: Get single article by filename
        if path.startswith('/api/article/'):
            filename = path.replace('/api/article/', '')
            article_path = DIRECTORY / 'articles' / filename

            if article_path.exists() and article_path.suffix == '.md':
                try:
                    content = article_path.read_text(encoding='utf-8')
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'content': content}, ensure_ascii=False).encode('utf-8'))
                except Exception as e:
                    self.send_error(500, str(e))
            else:
                self.send_error(404, 'Article not found')
            return

        # Serve static files normally
        return super().do_GET()

    def end_headers(self):
        # Add CORS headers for API endpoints
        if hasattr(self, '_cors_sent'):
            return
        self._cors_sent = True
        super().end_headers()


if __name__ == '__main__':
    print(f"Starting Obsidian English server at http://localhost:{PORT}")
    print(f"Serving files from: {DIRECTORY}")
    print(f"Reading articles from: {DIRECTORY / 'articles'}")
    print(f"\nAPI Endpoints:")
    print(f"  GET /api/articles     - List all articles from articles folder")
    print(f"  GET /api/article/name  - Get single article by filename")
    print(f"\nPress Ctrl+C to stop the server\n")

    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()
