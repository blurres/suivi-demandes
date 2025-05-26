import sys
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
from flask import jsonify
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

class Seminaire(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    reference  = db.Column(db.String(200), nullable=False, unique=True)
    theme      = db.Column(db.String(255), nullable=False, index=True)
    type_formation       = db.Column(db.String(200), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Demande(db.Model):
    __tablename__ = 'demandes'

    id = db.Column(db.Integer, primary_key=True)

    type = db.Column(db.String(100), nullable=False)
    reference = db.Column(db.String(100), nullable=False)
    theme = db.Column(db.String(200), nullable=False)

    civilite = db.Column(db.String(10), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenoms = db.Column(db.String(150), nullable=False)

    tels = db.Column(db.Text, nullable=True)
    emails = db.Column(db.Text, nullable=True)

    pays = db.Column(db.String(100), nullable=False)
    organisme = db.Column(db.String(150), nullable=False)
    contact = db.Column(db.String(150), nullable=True)

    lieu_formation = db.Column(db.String(150), nullable=False)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    duree = db.Column(db.String(50), nullable=False)

    date_recep_mail = db.Column(db.Date, nullable=False)
    date_accuse_recep = db.Column(db.Date, nullable=False)

    proforma = db.Column(db.String(20), nullable=False)  # 'sent' / 'not-sent'
    fiche_inscription = db.Column(db.String(20), nullable=False)  # 'received' / 'not-received'
    attestation = db.Column(db.String(20), nullable=False)  # 'sent' / 'not-sent'

    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('type', 'reference', 'theme', name='unique_type_ref_theme'),
    )



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


@app.route('/demandes', methods=['GET', 'POST'])
@login_required
def demandes():
    demandes = Demande.query.order_by(Demande.id.desc()).all()
    if request.method == 'POST' and request.is_json:
        data = request.get_json()

        if data.get('action') == 'get_references':
            type_name = data.get('type')
            references = (
                db.session.query(Seminaire.reference)
                .filter_by(type_formation=type_name)
                .distinct()
                .order_by(Seminaire.reference)
                .all()
            )
            return jsonify([r[0] for r in references])

        elif data.get('action') == 'get_themes':
            reference_name = data.get('reference')
            themes = (
                db.session.query(Seminaire.theme)
                .filter_by(reference=reference_name)
                .distinct()
                .order_by(Seminaire.theme)
                .all()
            )
            return jsonify([t[0] for t in themes])
        elif data.get('action') == 'get_organismes':
            country_name = data.get('pays')
            organismes = (
                db.session.query(Organisme.name)
                .filter_by(country=country_name)
                .distinct()
                .order_by(Organisme.name)
                .all()
            )
            return jsonify([o[0] for o in organismes])


        return jsonify({'error': 'Invalid action'}), 400

    types = TypeFormation.query.order_by(TypeFormation.name).all()

    lieux = LieuFormation.query.order_by(LieuFormation.name).all()
    countries = get_countries()
    return render_template('demandes.html', types=types, lieux=lieux, countries=countries, demandes=demandes)



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
    seminaires = Seminaire.query.order_by(Seminaire.reference).all()
    types = TypeFormation.query.order_by(TypeFormation.name).all()
    return render_template('seminaires.html', seminaires=seminaires, types=types)

@app.route('/operations', methods=['GET'])
@login_required
def operations():
    types = TypeFormation.query.order_by(TypeFormation.id).all()
    # get all seminaires (references and themes as dict)
    seminaires = Seminaire.query.order_by(Seminaire.reference).all()
    lieux = LieuFormation.query.order_by(LieuFormation.name).all()
    contacts = Demande.query.with_entities(Demande.contact).distinct().all()
    contacts = [c[0] for c in contacts]

    countries = get_countries()
    
    return render_template('operations.html', 
                           types=types, 
                           seminaires=seminaires,
                           countries=countries,
                           lieux=lieux,
                           contacts=contacts)


@app.route('/filtrer-demandes')
@login_required
def filtrer_demandes():
    query = Demande.query

    type_value = request.args.get('type')
    if type_value and type_value != 'all':
        query = query.filter(Demande.type == type_value)

    seminaire_value = request.args.get('seminaire')
    if seminaire_value and seminaire_value != 'all':
        query = query.filter(Demande.reference == seminaire_value)

    pays_value = request.args.get('pays')
    if pays_value and pays_value != 'all':
        query = query.filter(Demande.pays == pays_value)

    lieu_value = request.args.get('lieu')
    if lieu_value and lieu_value != 'all':
        query = query.filter(Demande.lieu_formation == lieu_value)

    contact_value = request.args.get('contact')
    if contact_value and contact_value != 'all':
        query = query.filter(Demande.contact == contact_value)

    # Récupération des dates
    debut = request.args.get('debut')
    fin = request.args.get('fin')
    
    # Logique de filtrage sur la date
    # 1) Si seul debut est fourni → filtre sur égalité sur date_debut
    # 2) Si seul fin est fourni → filtre sur égalité sur date_fin
    # 3) Si les deux sont fournis → filtre sur les demandes dont la date_debut est >= debut
    #    et dont la date_fin est <= fin (plage incluse)
    if debut and not fin:
        try:
            debut_date = datetime.strptime(debut, "%Y-%m-%d").date()
            query = query.filter(Demande.date_debut == debut_date)
        except ValueError:
            print(f"[DEBUG] Erreur de conversion pour 'debut': {debut}")
    elif fin and not debut:
        try:
            fin_date = datetime.strptime(fin, "%Y-%m-%d").date()
            query = query.filter(Demande.date_fin == fin_date)
        except ValueError:
            print(f"[DEBUG] Erreur de conversion pour 'fin': {fin}")
    elif debut and fin:
        try:
            debut_date = datetime.strptime(debut, "%Y-%m-%d").date()
            fin_date = datetime.strptime(fin, "%Y-%m-%d").date()
            query = query.filter(Demande.date_debut >= debut_date,
                                 Demande.date_fin <= fin_date)
        except ValueError:
            print(f"[DEBUG] Erreur de conversion pour 'debut' ou 'fin': {debut} / {fin}")

    demandes = query.all()
    result = []
    for d in demandes:
        result.append({
            "id": d.id,
            "type": d.type,
            "reference": d.reference,
            "theme": d.theme,
            "nom": d.nom,
            "prenoms": d.prenoms,
            "tels": d.tels,
            "emails": d.emails,
            "organisme": d.organisme,
            "pays": d.pays,
            "contact": d.contact,
            "lieu": d.lieu_formation,
            "debut": d.date_debut.strftime('%Y-%m-%d') if d.date_debut else '',
            "fin": d.date_fin.strftime('%Y-%m-%d') if d.date_fin else '',
            "duree": d.duree,
            "dateRecep": d.date_recep_mail.strftime('%Y-%m-%d') if d.date_recep_mail else "",
            "dateAccuseRecep": d.date_accuse_recep.strftime('%Y-%m-%d') if d.date_accuse_recep else "",
            "proforma": d.proforma,
            "fiche": d.fiche_inscription,
            "attestation": d.attestation
        })
    return jsonify(result)




@app.route('/filtrer-demandes-avances')
@login_required
def filtrer_demandes_avances():
    query = Demande.query

    types = request.args.getlist('types')
    seminaires = request.args.getlist('seminaires')
    debut = request.args.get('debut')
    fin = request.args.get('fin')

    print(f"[DEBUG] Types: {types}", file=sys.stderr)
    print(f"[DEBUG] Séminaires: {seminaires}", file=sys.stderr)
    print(f"[DEBUG] Dates: {debut} → {fin}", file=sys.stderr)

    if not (types or seminaires or debut or fin):
        return jsonify([])

    if types:
        query = query.filter(Demande.type.in_(types))
    if seminaires:
        query = query.filter(Demande.reference.in_(seminaires))

    # Application des filtres sur les dates
    if debut and not fin:
        try:
            debut_date = datetime.strptime(debut, "%Y-%m-%d").date()
            query = query.filter(Demande.date_debut == debut_date)
        except ValueError:
            print(f"[DEBUG] Erreur de conversion pour 'debut': {debut}", file=sys.stderr)
    elif fin and not debut:
        try:
            fin_date = datetime.strptime(fin, "%Y-%m-%d").date()
            query = query.filter(Demande.date_fin == fin_date)
        except ValueError:
            print(f"[DEBUG] Erreur de conversion pour 'fin': {fin}", file=sys.stderr)
    elif debut and fin:
        try:
            debut_date = datetime.strptime(debut, "%Y-%m-%d").date()
            fin_date = datetime.strptime(fin, "%Y-%m-%d").date()
            query = query.filter(Demande.date_debut >= debut_date,
                                 Demande.date_fin <= fin_date)
        except ValueError:
            print(f"[DEBUG] Erreur de conversion pour 'debut' ou 'fin': {debut} / {fin}", file=sys.stderr)

    demandes = query.all()

    result = [{
        "id": d.id,
        "type": d.type,
        "reference": d.reference,
        "theme": d.theme,
        "nom": d.nom,
        "prenoms": d.prenoms,
        "tels": d.tels,
        "emails": d.emails,
        "organisme": d.organisme,
        "pays": d.pays,
        "contact": d.contact,
        "lieu": d.lieu_formation,
        "debut": d.date_debut.strftime('%Y-%m-%d') if d.date_debut else '',
        "fin": d.date_fin.strftime('%Y-%m-%d') if d.date_fin else '',
        "duree": d.duree,
        "dateRecep": d.date_recep_mail.strftime('%Y-%m-%d') if d.date_recep_mail else "",
        "dateAccuseRecep": d.date_accuse_recep.strftime('%Y-%m-%d') if d.date_accuse_recep else "",
        "proforma": d.proforma,
        "fiche": d.fiche_inscription,
        "attestation": d.attestation
    } for d in demandes]

    return jsonify(result)




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
        organisme_ = Organisme(name=organisme, country=country)
        db.session.add(organisme_)
        try:
            db.session.commit()
            flash(f'Organisme ajouté avec succès!', 'success')
        except:
            db.session.rollback()
            flash('L\'enregistrement existe déjà!', 'danger')
    return redirect(url_for('organismes'))


@app.route('/organismes/<int:id>/edit', methods=['POST'])
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


# --------- Seminaires CRUD ---------
@app.route('/seminaires/create', methods=['POST'])
@login_required
def create_seminaire():
    reference = request.form.get('reference','').strip()
    theme = request.form.get('theme','').strip()
    type_formation = request.form.get('type','').strip()
    if not reference and not theme and not type_formation:
        flash('Tous les champs doivent être renseigné!', 'warning')
    else:
        sem = Seminaire(reference=reference, theme=theme, type_formation=type_formation)
        db.session.add(sem)
        try:
            db.session.commit()
            flash(f'Séminaire ajouté avec succès!', 'success')
        except:
            db.session.rollback()
            flash('Référence déjà utilisée!', 'danger')
    return redirect(url_for('seminaires'))


@app.route('/seminaires/<int:id>/edit',   methods=['POST'])
@login_required
def edit_seminaire(id):
    sem = Seminaire.query.get_or_404(id)
    new_reference = request.form.get('reference','').strip()
    new_theme = request.form.get('theme','').strip()
    new_type = request.form.get('type','').strip()
    if new_reference and new_theme and new_type:
        sem.reference = new_reference
        sem.theme = new_theme
        sem.type_formation = new_type
        db.session.commit()
        flash(f'Séminaire mis à jour avec succès!', 'success')
    else:
        flash('Tous les champs doivent être renseigné!', 'warning')
    return redirect(url_for('seminaires'))


@app.route('/seminaires/<int:id>/delete', methods=['POST'])
@login_required
def delete_seminaire(id):
    sem = Seminaire.query.get_or_404(id)
    db.session.delete(sem)
    db.session.commit()
    flash(f'Séminaire #{id} supprimé avec succès!', 'info')
    return redirect(url_for('seminaires'))


# --------- Demandes CRUD ---------
@app.route('/demandes/create', methods=['POST'])
@login_required
def create_demande():
    try:
        # Convert date inputs to datetime objects
        date_debut = datetime.strptime(request.form.get('debut', '').strip(), "%Y-%m-%d").date()
        date_fin = datetime.strptime(request.form.get('fin', '').strip(), "%Y-%m-%d").date()
        date_recep_mail = datetime.strptime(request.form.get('recep', '').strip(), "%Y-%m-%d").date()
        date_accuse_recep = datetime.strptime(request.form.get('accuseRecep', '').strip(), "%Y-%m-%d").date()
        
        # Ensure all required fields are received
        if not all([date_debut, date_fin, date_recep_mail, date_accuse_recep]):
            flash("Toutes les dates doivent être fournies!", "danger")
            return redirect(url_for('demandes'))

        # Create new Demande object
        demande = Demande(
            type=request.form.get('type', '').strip(),
            reference=request.form.get('reference', '').strip(),
            theme=request.form.get('theme', '').strip(),
            civilite=request.form.get('civilite', '').strip(),
            nom=request.form.get('nom', '').strip(),
            prenoms=request.form.get('prenoms', '').strip(),
            tels=request.form.get('tels', '').strip(),
            emails=request.form.get('emails', '').strip(),
            pays=request.form.get('pays', '').strip(),
            organisme=request.form.get('organisme', '').strip(),
            contact=request.form.get('contact', '').strip(),
            lieu_formation=request.form.get('lieu', '').strip(),
            date_debut=date_debut,
            date_fin=date_fin,
            duree=request.form.get('duree', '').strip(),
            date_recep_mail=date_recep_mail,
            date_accuse_recep=date_accuse_recep,
            proforma=request.form.get('proforma', '').strip(),
            fiche_inscription=request.form.get('fiche', '').strip(),
            attestation=request.form.get('attestation', '').strip()
        )

        # Add and commit to the database
        db.session.add(demande)
        db.session.commit()
        flash("Demande ajoutée avec succès!", "success")

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de l'ajout de la demande: {e}")
        flash("Une erreur s'est produite lors de l'ajout de la demande.", "danger")

    return redirect(url_for('demandes'))


@app.route('/demandes/<int:id>/edit', methods=['POST'])
@login_required
def edit_demande(id):
    demande = Demande.query.get_or_404(id)
    try:
        # Convert date inputs to datetime objects
        date_debut = datetime.strptime(request.form.get('debut', '').strip(), "%Y-%m-%d").date()
        date_fin = datetime.strptime(request.form.get('fin', '').strip(), "%Y-%m-%d").date()
        date_recep_mail = datetime.strptime(request.form.get('recep', '').strip(), "%Y-%m-%d").date()
        date_accuse_recep = datetime.strptime(request.form.get('accuseRecep', '').strip(), "%Y-%m-%d").date()

        # Update Demande object
        demande.type = request.form.get('type', '').strip()
        demande.reference = request.form.get('reference', '').strip()
        demande.theme = request.form.get('theme', '').strip()
        demande.civilite = request.form.get('civilite', '').strip()
        demande.nom = request.form.get('nom', '').strip()
        demande.prenoms = request.form.get('prenoms', '').strip()
        demande.tels = request.form.get('tels', '').strip()
        demande.emails = request.form.get('emails', '').strip()
        demande.pays = request.form.get('pays', '').strip()
        demande.organisme = request.form.get('organisme', '').strip()
        demande.contact = request.form.get('contact', '').strip()
        demande.lieu_formation = request.form.get('lieu', '').strip()
        demande.date_debut = date_debut
        demande.date_fin = date_fin
        demande.duree = request.form.get('duree', '').strip()
        demande.date_recep_mail = date_recep_mail
        demande.date_accuse_recep = date_accuse_recep
        demande.proforma = request.form.get('proforma', '').strip()
        demande.fiche_inscription = request.form.get('fiche', '').strip()
        demande.attestation = request.form.get('attestation', '').strip()

        # Commit changes to the database
        db.session.commit()
        flash("Demande mise à jour avec succès!", "success")

    except Exception as e:
        db.session.rollback()
        print(f"Erreur lors de la mise à jour de la demande: {e}")
        flash("Une erreur s'est produite lors de la mise à jour de la demande.", "danger")

    return redirect(url_for('demandes'))


@app.route('/demandes/<int:id>/delete', methods=['POST'])
@login_required
def delete_demande(id):
    demande = Demande.query.get_or_404(id)
    db.session.delete(demande)
    db.session.commit()
    flash(f'Demande #{id} supprimée!', 'info')
    return redirect(url_for('demandes'))


if __name__ == '__main__':
    if not os.path.exists('db.sqlite3'):
        with app.app_context():
            db.create_all()
            # create default admin
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin')
                admin.set_password('Ideca@2025')
                db.session.add(admin)
                db.session.commit()
                print("DB & admin user initialized")
    app.run()
