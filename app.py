from flask import Flask, request, render_template, redirect, url_for
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
import secrets

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rprocess58@gmail.com'
app.config['MAIL_PASSWORD'] = 'adxj cpnb fnua lwaq'
app.app_context().push()
mail = Mail(app)
db = SQLAlchemy(app)


@app.route('/', endpoint='mainpage', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


def generate_confirmation_code():
    return secrets.token_hex(6)


class EmailConfirmation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    confirmation_code = db.Column(db.String(120), nullable=False, unique=True)


def send_confirmation_code(to_email, confirmation_code):
    msg = Message('Подтверждение регистрации',
                  sender='your-email@gmail.com',
                  recipients=[to_email])
    msg.body = f'Ваш код подтверждения: {confirmation_code}'
    mail.send(msg)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    confirmed = db.Column(db.Boolean, default=False)

    def send_confirmation_code(self):
        confirmation_code = generate_confirmation_code()
        email_confirmation = EmailConfirmation(user_id=self.id, confirmation_code=confirmation_code)
        db.session.add(email_confirmation)
        db.session.commit()
        send_confirmation_code(self.email, confirmation_code)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if the user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # Return an error if the user already exists
            return render_template('login.html')
        else:
            # Create a new user if the user does not exist
            user = User(username=username, password=password, email=email)
            db.session.add(user)
            db.session.commit()
            # Send the confirmation code to the user's email address
            confirmation_code = generate_confirmation_code()
            email_confirmation = EmailConfirmation(user_id=user.id, confirmation_code=confirmation_code)
            db.session.add(email_confirmation)
            db.session.commit()
            send_confirmation_code(user.email, confirmation_code)
            # Redirect to the confirm_email page with the confirmation code
            return render_template('confirmation_sent.html', confirmation_code=confirmation_code)
    return render_template('register.html')


@app.route('/confirm-email/<confirmation_code>', methods=['GET', 'POST'])
def confirm_email(confirmation_code):
    email_confirmation = EmailConfirmation.query.filter_by(confirmation_code=confirmation_code).first()
    if email_confirmation:
        user = User.query.get(email_confirmation.user_id)
        if user.confirmed:
            db.session.delete(email_confirmation)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            if request.method == 'POST':
                entered_confirmation_code = request.form['confirmation_code']
                if entered_confirmation_code == confirmation_code:
                    user.confirmed = True
                    db.session.delete(email_confirmation)
                    db.session.commit()
                    return render_template('confirmed.html')
                else:
                    return 'Неправильный код подтверждения.'
    else:
        return 'Код подтверждения не существует.'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if user.confirmed:
                if user.password == password and user.username == username:
                    return render_template('index.html')
                else:
                    return '''Неправильный пароль. <a href="/login" class="btn btn-secondary"><button type="button" 
                    class="btn btn-primary">Вернуться к логину</button></a>'''
            else:
                return '''Неактивная учётная запись. <a href="/" class="btn btn-secondary"><button type="button" 
                class="btn btn-primary">Вернуться к регистрации</button></a>'''
        else:
            return '''Неправильное имя пользователя. <a href="/login" class="btn btn-secondary"><button type="button" 
            class="btn btn-primary">Вернуться к логину</button></a>'''
    return render_template('login.html')


if __name__ == '__main__':
    app.run()
