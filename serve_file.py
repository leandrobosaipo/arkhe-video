#!/usr/bin/env python3
"""Servidor HTTP simples para servir arquivos locais durante testes"""
import http.server
import socketserver
import os
import sys

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Define o diretório base como o diretório de Downloads
        self.directory = "/Users/leandrobosaipo/Downloads"
        super().__init__(*args, directory=self.directory, **kwargs)
    
    def log_message(self, format, *args):
        """Override para log mais limpo"""
        print(f"[Servidor] {args[0]}")

if __name__ == "__main__":
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[Servidor] Servindo arquivos em http://localhost:{PORT}/")
        print(f"[Servidor] Pressione Ctrl+C para parar")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[Servidor] Parando servidor...")
            sys.exit(0)

