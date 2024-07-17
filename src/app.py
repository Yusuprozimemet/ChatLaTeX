from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess
import yaml
from chatbot import Chatbot

app = Flask(__name__)

# Load configuration from config.yaml
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Initialize Chatbot with the path to your YAML configuration file
chatbot = Chatbot.from_config('config.yaml')

# Get xelatex path from the configuration
xelatex_path = config.get('xelatex_path')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    latex_code = request.form['latex']

    # Ensure the LaTeX code has the necessary structure
    if not latex_code.startswith(r'\documentclass'):
        latex_code = r'\documentclass{article}\begin{document}' + latex_code + r'\end{document}'

    # Save LaTeX code to latex_document.tex in the static folder
    with open('static/latex_document.tex', 'w') as f:
        f.write(latex_code)

    # Convert LaTeX to PDF using xelatex
    try:
        subprocess.run([xelatex_path, '-output-directory', 'static', 'static/latex_document.tex'], check=True)
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
    try:
        with open('static/latex_document.tex', 'r') as f:
            latex_code = f.read()
        combined_prompt = f"Here's the LaTeX document:\n\n{latex_code}\n\nUser command:\n{prompt}"
        chatbot.add_message("user", combined_prompt)
        response = chatbot.send_request()
        return jsonify(response=response)
    except FileNotFoundError:
        return jsonify(response="LaTeX document not found.")
    except Exception as e:
        return jsonify(response=str(e))

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
