from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        message = request.form.get('user_message')
        if message:
            with open('messages.txt', 'a', encoding='utf-8') as file:
                file.write(message + '\n')
        return redirect('/')

    try:
        with open('messages.txt', 'r', encoding='utf-8') as file:
            saved_messages = file.readlines()
            # The Magic Word: This flips the list upside down so newest is first
            saved_messages.reverse() 
    except FileNotFoundError:
        saved_messages = []

    return render_template('index.html', messages=saved_messages)

if __name__ == '__main__':
    app.run(debug=True)

