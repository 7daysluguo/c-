#!/usr/bin/env python3
"""
文件保存处理器 - 保存文件并推送到 GitHub
"""
import os
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi

class SaveHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        """处理 HEAD 请求"""
        if self.path == '/demo-editor.html' or self.path == '/demo.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/demo-editor.html':
            # 返回编辑器页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('demo-editor.html', 'rb') as f:
                self.wfile.write(f.read())
        elif self.path == '/demo.html':
            # 返回 demo.html 内容
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            if os.path.exists('demo.html'):
                with open('demo.html', 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b'File not found')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求 - 保存文件"""
        if self.path == '/save-demo.html':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # 解析表单数据
            try:
                # 尝试解析 JSON
                data = json.loads(post_data.decode('utf-8'))
                content = data.get('content', '')
            except:
                # 如果不是 JSON，尝试解析表单数据
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                content = form.getvalue('content', '')
            
            if not content:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '内容为空'}).encode())
                return
            
            try:
                # 保存文件
                with open('demo.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 添加到 Git
                subprocess.run(['git', 'add', 'demo.html'], 
                             cwd='/workspace', 
                             check=True, 
                             capture_output=True)
                
                # 提交
                result = subprocess.run(
                    ['git', 'commit', '-m', 'Update demo.html from web editor'],
                    cwd='/workspace',
                    capture_output=True,
                    text=True
                )
                
                # 推送到 GitHub
                push_result = subprocess.run(
                    ['git', 'push', 'origin', 'HEAD'],
                    cwd='/workspace',
                    capture_output=True,
                    text=True
                )
                
                if push_result.returncode == 0:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'message': '文件已保存并推送到 GitHub！'
                    }).encode())
                else:
                    # 即使推送失败，文件也已保存
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'message': '文件已保存，但推送可能失败',
                        'push_error': push_result.stderr
                    }).encode())
                    
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': str(e)
                }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """禁用默认日志"""
        pass

def run_server(port=8001):
    """启动服务器"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, SaveHandler)
    print(f'服务器运行在 http://0.0.0.0:{port}')
    print(f'编辑器地址: http://localhost:{port}/demo-editor.html')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
