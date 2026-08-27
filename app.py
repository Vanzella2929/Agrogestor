from flask import Flask, render_template

app = Flask(_name_)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/animais')
def animais():
    return render_template('animais.html')

@app.route('/custos')
def custos():
    return render_template('custos.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

if _name_ == '_main_':
    app.run(debug=True)