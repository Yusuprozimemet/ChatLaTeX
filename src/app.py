from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess
from chatbot import Chatbot

app = Flask(__name__)

# Initialize Chatbot with the path to your YAML configuration file
chatbot = Chatbot.from_config('config.yaml')

# Update this with the path to pdflatex from MiKTeX
pdflatex_path = r'C:\Users\yosef\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    latex_code = request.form['latex']

    # Save LaTeX code to latex_document.tex in the static folder
    with open('static/latex_document.tex', 'w') as f:
        f.write(latex_code)

    # Convert LaTeX to PDF
    try:
        subprocess.run([pdflatex_path, '-output-directory', 'static', 'static/latex_document.tex'], check=True)
        return jsonify(success=True, latex=latex_code)
    except subprocess.CalledProcessError as e:
        return jsonify(success=False, error=str(e))


@app.route('/pdf')
def pdf():
    return send_file('static/latex_document.pdf')

@app.route('/latex')
def get_latex():
    try:
        with open('static/latex_document.tex', 'r') as f:
            latex_code = f.read()
        return jsonify(success=True, latex=latex_code)
    except FileNotFoundError:
        return jsonify(success=False, error="LaTeX document not found.")


@app.route('/ask', methods=['POST'])
def ask():
    prompt = request.form['prompt']
    chatbot.add_message("user", prompt)
    try:
        response = chatbot.send_request()
        return jsonify(response=response)
    except Exception as e:
        return jsonify(response=str(e))

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
