from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import csv
import locale
locale.setlocale(locale.LC_ALL, '')


def get_countries():
    countries = []
    with open('./instance/countries.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            countries.append(row['name'])
    countries.sort(key=locale.strxfrm)
    return countries

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'


# --------- Models ---------
class User(db.Model, UserMixin):
    id            = db.Column(db.Integer,   primary_key=True)
    username      = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime,   default=datetime.now)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class TypeFormation(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)


class LieuFormation(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Organisme(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False, unique=True)
    country    = db.Column(db.String(200), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)


# --------- Login Loader ---------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --------- Auth Routes ---------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('demandes'))

    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = User.query.filter_by(username=u).first()
        if user and user.check_password(p):
            login_user(user)
            flash(f'Bienvenue, {u}', 'success')
            return redirect(request.args.get('next') or url_for('demandes'))
        flash('Identifiants invalides!', 'danger')

    return render_template('index.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté.", 'info')
    return redirect(url_for('login'))


@app.route('/demandes', methods=['GET'])
@login_required
def demandes():
    return render_template('demandes.html')

@app.route('/organismes', methods=['GET'])
@login_required
def organismes():
    organismes_list = Organisme.query.with_entities(Organisme.id, Organisme.name, Organisme.country).order_by(Organisme.name).all()
    countries = get_countries()
    return render_template('organisme.html', organismes=organismes_list, countries=countries)


@app.route('/utilisateurs', methods=['GET'])
@login_required
def utilisateurs():
    return render_template('utilisateurs.html')

@app.route('/seminaires', methods=['GET'])
@login_required
def seminaires():
    return render_template('seminaires.html')

@app.route('/operations', methods=['GET'])
@login_required
def operations():
    return render_template('operations.html')


# --------- Types CRUD Routes ---------
@app.route('/types_de_formation', methods=['GET'])
@login_required
def types_de_formation():
    types = TypeFormation.query.order_by(TypeFormation.id).all()
    return render_template('types_de_formation.html', types=types)

@app.route('/lieux_de_formation', methods=['GET'])
@login_required
def lieux_de_formation():
    lieux = LieuFormation.query.order_by(LieuFormation.id).all()
    return render_template('lieux_de_formation.html', lieux=lieux)


# --------- Type Formation CRUD ---------
@app.route('/types_de_formation/create', methods=['POST'])
@login_required
def create_type():
    name = request.form.get('name','').strip()
    if not name:
        flash('Le nom ne peut être vide!', 'warning')
    else:
        tf = TypeFormation(name=name)
        db.session.add(tf)
        try:
            db.session.commit()
            flash(f'Type “{name}” ajouté.', 'success')
        except:
            db.session.rollback()
            flash('Ce type existe déjà.', 'danger')
    return redirect(url_for('types_de_formation'))


@app.route('/types_de_formation/<int:id>/edit',   methods=['POST'])
@login_required
def edit_type(id):
    tf = TypeFormation.query.get_or_404(id)
    new_name = request.form.get('name','').strip()
    if new_name:
        tf.name = new_name
        db.session.commit()
        flash(f'Type mis à jour avec succès!', 'success')
    else:
        flash('Le nom ne peut être vide!', 'warning')
    return redirect(url_for('types_de_formation'))


@app.route('/types_de_formation/<int:id>/delete', methods=['POST'])
@login_required
def delete_type(id):
    tf = TypeFormation.query.get_or_404(id)
    db.session.delete(tf)
    db.session.commit()
    flash(f'Type #{id} supprimé!', 'info')
    return redirect(url_for('types_de_formation'))


# --------- Lieu Formation CRUD ---------
@app.route('/lieux_de_formation/create', methods=['POST'])
@login_required
def create_lieu():
    name = request.form.get('name','').strip()
    if not name:
        flash('Le nom ne peut être vide!', 'warning')
    else:
        tf = LieuFormation(name=name)
        db.session.add(tf)
        try:
            db.session.commit()
            flash(f'Lieu “{name}” ajouté.', 'success')
        except:
            db.session.rollback()
            flash('Ce lieu existe déjà.', 'danger')
    return redirect(url_for('lieux_de_formation'))


@app.route('/lieux_de_formation/<int:id>/edit',   methods=['POST'])
@login_required
def edit_lieu(id):
    tf = LieuFormation.query.get_or_404(id)
    new_name = request.form.get('name','').strip()
    if new_name:
        tf.name = new_name
        db.session.commit()
        flash(f'Lieu mis à jour avec succès!', 'success')
    else:
        flash('Le nom ne peut être vide!', 'warning')
    return redirect(url_for('lieux_de_formation'))


@app.route('/lieux_de_formation/<int:id>/delete', methods=['POST'])
@login_required
def delete_lieu(id):
    tf = LieuFormation.query.get_or_404(id)
    db.session.delete(tf)
    db.session.commit()
    flash(f'Lieu #{id} supprimé!', 'info')
    return redirect(url_for('lieux_de_formation'))


# --------- Organisme CRUD ---------
@app.route('/organismes/create', methods=['POST'])
@login_required
def create_organisme():
    organisme = request.form.get('organisme','').strip()
    country = request.form.get('pays','').strip()
    if not organisme or not country:
        flash('Tous champs doivent être renseigné!', 'warning')
    else:
        tf = Organisme(name=organisme, country=country)
        db.session.add(tf)
        try:
            db.session.commit()
            flash(f'Organisme ajouté avec succès!', 'success')
        except:
            db.session.rollback()
            flash('L\'enregistrement existe déjà!', 'danger')
    return redirect(url_for('organismes'))


@app.route('/organismes/<int:id>/edit',   methods=['POST'])
@login_required
def edit_organisme(id):
    tf = Organisme.query.get_or_404(id)
    new_name = request.form.get('organisme','').strip()
    new_country = request.form.get('pays','').strip()
    if new_name and new_country:
        tf.name = new_name
        tf.country = new_country
        db.session.commit()
        flash(f'Organisme mis à jour avec succès!', 'success')
    else:
        flash('Tous les champs doivent être renseigné!', 'warning')
    return redirect(url_for('organismes'))


@app.route('/organismes/<int:id>/delete', methods=['POST'])
@login_required
def delete_organisme(id):
    tf = Organisme.query.get_or_404(id)
    db.session.delete(tf)
    db.session.commit()
    flash(f'Organisme #{id} supprimé!', 'info')
    return redirect(url_for('organismes'))


@app.route('/test')
def test():
    return render_template('test')


if __name__ == '__main__':
    if not os.path.exists('db.sqlite3'):
        with app.app_context():
            db.create_all()
            # create default admin
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("DB & admin user initialized")
    app.run(debug=True, host='0.0.0.0', port=5000)
