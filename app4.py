from flask import *
from functools import wraps
import mysql.connector
from mysql.connector import Error
from flask_mysqldb import MySQL
import pdfkit
import hashlib
import smtplib
from email.message import EmailMessage
app = Flask(__name__)
def get_len(obj):
    return len(obj)

app.jinja_env.globals.update(len=len)

# ou bien

app.jinja_env.filters['len'] = len
app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = 'kf2023'


def sha256sum(filename):
   # h = hashlib.sha256()
   # b = bytearray(128*1024)
    #mv = memoryview(b)
    #with open(filename, 'rb', buffering=0) as f:
     #   for n in iter(lambda: f.readinto(mv), 0):
      #      h.update(mv[:n])
      
    hasher = hashlib.sha256()
    with open(filename, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
        print(hasher.hexdigest())
        return hasher.hexdigest()


def connect_db():
    connection = mysql.connector.connect(
         host='localhost', 
         database='releves_notes',
         user='root', 
         password='');
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)
    return connection;    

@app.before_request
def before_request():
    g.db = connect_db()

def login_required(test):
	@wraps(test)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return test(*args, **kwargs)
		else:
			flash('You need to login first.')
			return redirect(url_for('log'))
	return wrap	

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('profil', None)
    session.pop('name', None)
    flash('You were logged out')
    return redirect (url_for('log'))

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/contac', methods=['GET', 'POST'])
def contac():
    if request.method == 'POST':
        sender = "fatifarno2002@gmail.com"
        receiver = "farnounef@gmail.com"
        password = "nyewikfluvfvrkcy"
        name = request.form['name']
        email = request.form['email']
        
        message = request.form['message']

        # Créer un objet EmailMessage et définir les champs "From", "To" et "Subject"
        msg = EmailMessage()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = "message depuis la page de contact"

        # Ajouter le corps du message
        msg.set_content(f"Nom: {name}\nEmail: {email}\n\n{message}")

        # Créer un serveur SMTP et envoyer le message
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        

    return render_template('contact.html')


def connectTo():
    error = None
    if request.method == 'POST':
        g.db  = connect_db() #se connecte à la base de données 
        cursor = g.db.cursor()
        cursor.execute("SELECT profil, nom, prenom, password, CNE, CIN, naissance, lieux, adresse, email, gsm, id_filiere FROM user WHERE CNE='" + request.form['profil'] + "'")
        record = cursor.fetchone()#récupère le premier enregistrement de la requête exécutée précédemment
        cursor.execute("SELECT email_prof, password FROM professeur WHERE email_prof='" + request.form['profil'] + "'")
        record1 = cursor.fetchone()#récupère le premier enregistrement de la requête exécutée précédemment
        cursor.execute("SELECT email_admin, password FROM admin WHERE email_admin='" + request.form['profil'] + "'")
        record2 = cursor.fetchone()#récupère le premier enregistrement de la requête exécutée précédemment

        
        if record is not None:
            profil, nom, prenom, password, CNE, CIN, naissance, lieux, adresse, email, gsm, id_filiere = record
            g.db.close()

            if password == request.form['password']:
                session['logged_in'] = True
                session['profil'] = profil
                session['CNE'] = CNE
                session['name'] = nom + " " + prenom
                return redirect(url_for('accueil_etudiant'))
            else:
                error = "L'utilisateur ou le mot de passe sont incorrects" 
        elif record1 is not None:
            email_prof,password=record1
            g.db.close()
            if password == request.form['password']:
                session['logged_in'] = True
                session['email']=email_prof
                return redirect(url_for('accprof'))
        elif record2 is not None:
            email_admin,password=record2
            g.db.close()
            if password == request.form['password']:
                session['logged_in'] = True
                return redirect(url_for('accueil_admin'))    
        else:
            error = "L'utilisateur ou le mot de passe sont incorrects" 

            
    return render_template('log.html', error=error)

#//////////////////////////ETUDIANT/////////////////////////
@app.route("/accueil_etudiant")
@login_required
def accueil_etudiant():
    nom = session.get('name')
    CNE = session.get('CNE')
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT nom, prenom, CNE,CIN, naissance, lieux, adresse, email, gsm, filiere.nom_filiere FROM user JOIN filiere ON user.id_filiere = filiere.id_filiere WHERE CNE='" + CNE + "'")
    record = cursor.fetchone()
    g.db.close()
    if record is not None:
        nom, prenom, CNE, CIN, naissance, lieux, adresse, email, gsm, filiere = record
        return render_template('accueil_etudiant.html', nom=nom, prenom=prenom, CNE=CNE, CIN=CIN, filiere=filiere, naissance=naissance, lieux=lieux, adresse=adresse, email=email, gsm=gsm)
    else:
        return render_template('accueil_etudiant.html')
 

@app.route("/note_etudiant")
@login_required
def note_etudiant():
    CNE = session.get('CNE')
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("""
        SELECT 
            module.nom_module, 
            GROUP_CONCAT(matiere.nom_matiere SEPARATOR ', ') AS matieres, 
            GROUP_CONCAT(IFNULL(max_notematiere.note_notematiere, 'en cours') SEPARATOR ', ') AS notes
        FROM 
            user
            JOIN filiere ON filiere.id_filiere = user.id_filiere
            JOIN module ON module.id_filiere = filiere.id_filiere
            JOIN matiere ON matiere.id_module = module.id_module 
            LEFT JOIN (
                SELECT id_matiere, note_notematiere 
                FROM notematiere 
                WHERE id_notematiere IN (
                    SELECT MAX(id_notematiere) 
                    FROM notematiere 
                    WHERE id IN (
                        SELECT id 
                        FROM user 
                        WHERE CNE = %s
                    )
                    GROUP BY id_matiere
                )
            ) AS max_notematiere ON max_notematiere.id_matiere = matiere.id_matiere
        WHERE 
            user.CNE = %s
        GROUP BY 
            module.nom_module;
    """, (CNE, CNE,))
    results = cursor.fetchall()
    g.db.close()
    return render_template('note_etudiant.html', results=results)

@app.route("/relevenote_etudiant")
@login_required
def relevenote_etudiant():
    CNE = session.get('CNE')
    g.db = connect_db()
    cursor = g.db.cursor()

    # Vérifier si des données existent pour l'étudiant
    cursor.execute("""
        SELECT COUNT(*) 
        FROM relevenote 
        JOIN notemodule ON relevenote.id_notemodule = notemodule.id_notemodule 
        WHERE relevenote.id = (SELECT id FROM user WHERE CNE=%s)
    """, (CNE,))
    has_data = cursor.fetchone()[0] > 0

    if not has_data:
        g.db.close()
        return render_template('pas_releve_etudiant.html')

    # Récupérer les informations de l'étudiant
    cursor.execute("SELECT id FROM user WHERE CNE=%s", (CNE,))
    id = cursor.fetchone()[0]
    cursor.execute("SELECT id_filiere FROM user WHERE CNE=%s", (CNE,))
    id_filiere = cursor.fetchone()[0]
    cursor.execute("SELECT nom_filiere FROM filiere WHERE id_filiere=%s", (id_filiere,))
    filiere = cursor.fetchone()[0]
    cursor.execute("SELECT nom, prenom, CNE, CIN, naissance FROM user WHERE CNE=%s", (CNE,))
    etudiant = dict(zip(['nom', 'prenom', 'CNE', 'CIN', 'naissance'], cursor.fetchone()))
    etudiant['id'] = id
    etudiant['id_filiere'] = id_filiere
    etudiant['filiere'] = filiere
    
    cursor.execute("""
        SELECT module.nom_module, notemodule.note_notemodule, AVG(notemodule.note_notemodule) 
        FROM relevenote 
        JOIN module ON relevenote.id_module = module.id_module 
        JOIN notemodule ON relevenote.id_notemodule = notemodule.id_notemodule 
        WHERE relevenote.id = %s AND relevenote.id_relevenote IN (
            SELECT MAX(id_relevenote) FROM relevenote WHERE id = %s GROUP BY id_module
        )
        GROUP BY module.nom_module 
    """, (id, id))
    results = cursor.fetchall()
 
    moyenne_generale = round(sum([r[2] for r in results]) / len(results), 2) # Calcul de la moyenne générale sur tous les modules
    g.db.close()
    return render_template('relevenote_etudiant.html',etudiant=etudiant, results=results, moyenne_generale=moyenne_generale)
    
#//////////////////////////ADMIN/////////////////////////
@app.route('/hasher_PDF')
def hasher_PDF():
    return render_template('hasher_PDF.html')
#////////////Entreprise////////////
@app.route('/upload', methods=['POST'])
def upload_file():
    # Get the uploaded file from the request
    file = request.files['file']
    
    # Read the file contents
    file_contents = file.read()
    
    # Calculate the SHA-256 hash of the file
    file_hash = hashlib.sha256(file_contents).hexdigest()
    
    # Return the hash as a response
    return render_template('verification_hash.html',hash=file_hash)
#//////////////////////////////////

@app.route("/accueil_admin")
@login_required
def accueil_admin():
    #nombreEtudiants
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT COUNT(*) AS total_etudiants FROM user")
    nombreEtudiants = cursor.fetchall()
    nombreEtudiants = list(map(lambda x: x[0], nombreEtudiants))
    g.db.close()
    #nombreprofesseurs
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT COUNT(*) AS total_professeurs FROM professeur")
    nombreProfesseurs = cursor.fetchall()
    nombreProfesseurs = list(map(lambda x: x[0], nombreProfesseurs))
    g.db.close()
     
    return render_template('accueil_admin.html',nombreEtudiants=nombreEtudiants,nombreProfesseurs=nombreProfesseurs)
 
@app.route("/filieres")
@login_required
def accueil_filiere():
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT id_filiere from filiere")
    record4 = cursor.fetchall()
    # Utilisez la méthode map pour convertir la liste de tuples en liste d'entiers
    record4 = list(map(lambda x: x[0], record4))
    g.db.close()
    return render_template('listesfilieres.html',record4=record4)

@app.route('/filiere_eleve/<filiere>', methods=['GET', 'POST'])
@login_required

def filiere_eleve(filiere):
   
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT id,profil,nom,password,CNE,CIN,naissance,lieux,adresse,email,gsm,niveau,id_filiere,id_semestre,prenom FROM user where id_filiere= %s", [filiere])
    records = cursor.fetchall()
    g.db.close()
    #afficher le nom de la filiere
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT nom_filiere FROM filiere where id_filiere= %s", [filiere])
    records1 = cursor.fetchall()
    records1 = list(map(lambda x: x[0], records1))
    g.db.close()

    data_niveau = []
    
    for record in records:
        etudiant = {}
        etudiant['id'] = record[0]
        etudiant['profil'] = record[1]
        etudiant['nom'] = record[2]
        etudiant['password'] = record[3]
        etudiant['CNE'] = record[4]
        etudiant['CIN'] = record[5]
        etudiant['naissance'] = record[6]
        etudiant['lieux'] = record[7]
        etudiant['adresse'] = record[8]
        etudiant['email'] = record[9]
        etudiant['gsm'] = record[10]
        etudiant['niveau'] = record[11]
        etudiant['id_filiere'] = record[12]
        etudiant['id_semestre'] = record[13]
        etudiant['prenom'] = record[14]

        data_niveau.append(etudiant)
    
    return render_template("index.html", data_niveau=data_niveau,filiere=filiere,records1=records1)

@app.route('/insert/<filiere>', methods = ['POST'])
def insert(filiere):
    if request.method == "POST":
        
        nom = request.form['nom']
        prenom = request.form['prenom']
        password = request.form['password']
        cne = request.form['cne']
        cin = request.form['cin']
        email = request.form['email']
        semestre=request.form['semestre']
        gsm = request.form['gsm']
        niveau= request.form['niveau']
        naissance=request.form['naissance']
        lieux=request.form['lieux']
        adresse=request.form['adresse']

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO user (nom, prenom,password,CNE,CIN,email,gsm,id_filiere,id_semestre,niveau,naissance,lieux,adresse) VALUES (%s, %s, %s, %s, %s, %s, %s,%s,%s,%s,%s,%s,%s)", (nom, prenom,password,cne,cin,email,gsm,filiere,semestre,niveau,naissance,lieux,adresse))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('filiere_eleve',filiere=filiere))


@app.route('/update/<filiere>', methods= ['POST', 'GET'])
def update(filiere):
    if request.method == 'POST':

        id = request.form['id']
        nom = request.form['nom']
        naissance = request.form['naissance']
        lieux = request.form['lieux']
        cne = request.form['cne']
        cin = request.form['cin']
        adresse = request.form['adresse']
        email = request.form['email']
        gsm = request.form['gsm']
        prenom=request.form['prenom']

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("""
        UPDATE user SET nom=%s, CNE=%s,CIN=%s,naissance=%s,lieux=%s,adresse=%s,email=%s,gsm=%s,prenom=%s
        WHERE id=%s
        """, (nom, cne, cin, naissance,lieux,adresse,email,gsm,prenom,id))
        connection.commit()

    # Fermer la connexion à la base de données
        cursor.close()
        connection.close()
        
        return redirect(url_for('filiere_eleve', filiere=filiere))


@app.route('/delete/<string:id_fil>/<string:id_data>', methods = ['GET'])
def delete(id_fil,id_data):
    
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute(" DELETE FROM user WHERE id=%s", (id_data,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('filiere_eleve',filiere=id_fil))

#crud professeur
@app.route("/professeurs")
@login_required
def professeurs():
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT id_prof,nom_prof,prenom_prof,email_prof,password FROM professeur")
    professeurs = cursor.fetchall()
    g.db.close()
    return render_template('index2.html', professeurs=professeurs)


@app.route('/inserer', methods = ['POST'])
def inserer():
    if request.method == "POST":
       
        nom = request.form['nom']
        prenom= request.form['prenom']
        email = request.form['email']
        password = request.form['password']

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO professeur (nom_prof, prenom_prof, email_prof,password) VALUES (%s, %s, %s,%s)", (nom, prenom,email,password))
        
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('professeurs'))

@app.route('/supprimer/<string:id_data>', methods = ['GET'])
def supprimer(id_data):
   
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM professeur WHERE id_prof=%s", (id_data,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('professeurs'))    

@app.route('/modifier', methods= ['POST', 'GET'])
def modifier():
    if request.method == 'POST':
        id_data = request.form['id']
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        password = request.form['password']

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("""
        UPDATE professeur SET nom_prof=%s, prenom_prof=%s, email_prof=%s,password=%s
        WHERE id_prof=%s
        """, (nom, prenom, email, password,id_data))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect(url_for('professeurs'))


@app.route("/generer_relevé")
@login_required
def generer_relevé():
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT id_filiere from filiere")
    record4 = cursor.fetchall()
    # Utilisez la méthode map pour convertir la liste de tuples en liste d'entiers
    record4 = list(map(lambda x: x[0], record4))  
    g.db.close()
    return render_template('generer_relevé.html',record4=record4)



@app.route('/filiere_eleve_generer_relevé/<filiere>', methods=['GET', 'POST'])
@login_required
def filiere_eleve_generer_relevé(filiere):
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("""
    SELECT user.nom, user.niveau, user.CNE, relevenote.id
    FROM user
    LEFT JOIN relevenote ON user.id = relevenote.id
    WHERE user.id_filiere = %s
    """, [filiere])
    records = cursor.fetchall()

    data_niveau1 = {}
    data_niveau2 = {}
    data_niveau3 = {}

    for record in records:
        nom_etudiant = record[0]
        niveau = record[1]
        cne_etudiant = record[2]
        id_relevenote = record[3]
        is_disabled = id_relevenote is not None

        if niveau == 1:
            data_niveau1[nom_etudiant] = {'niveau': niveau, 'cne': cne_etudiant, 'is_disabled': is_disabled}
        elif niveau == 2:
            data_niveau2[nom_etudiant] = {'niveau': niveau, 'cne': cne_etudiant, 'is_disabled': is_disabled}
        elif niveau == 3:
            data_niveau3[nom_etudiant] = {'niveau': niveau, 'cne': cne_etudiant, 'is_disabled': is_disabled}

    #hashpdf=sha256sum("PDFs/Hachem_Safae_2ite_Niveau1.pdf")
    g.db.close()
    return render_template("filiere_eleve_generer_relevé.html", data_niveau1=data_niveau1, data_niveau2=data_niveau2, data_niveau3=data_niveau3)


@app.route('/relevenote_admin/<cne>', methods=['GET', 'POST'])
@login_required
def relevenote_admin(cne):
    g.db = connect_db()
    cursor = g.db.cursor()
    config = pdfkit.configuration(wkhtmltopdf="D:\\SFS\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    # Récupérer les informations de l'étudiant
    cursor.execute("SELECT id FROM user WHERE CNE=%s", (cne,))
    id = cursor.fetchone()[0]
    cursor.execute("SELECT niveau FROM user WHERE CNE=%s", (cne,))
    niveau = cursor.fetchone()[0]
    cursor.execute("SELECT id_filiere FROM user WHERE CNE=%s", (cne,))
    id_filiere = cursor.fetchone()[0]
    cursor.execute("SELECT nom_filiere FROM filiere WHERE id_filiere=%s", (id_filiere,))
    filiere = cursor.fetchone()[0]
    cursor.execute("SELECT nom, prenom, CNE, CIN, naissance FROM user WHERE CNE=%s", (cne,))
    etudiant = dict(zip(['nom', 'prenom', 'CNE', 'CIN', 'naissance'], cursor.fetchone()))
    etudiant['id'] = id
    etudiant['id_filiere'] = id_filiere
    etudiant['filiere'] = filiere
    etudiant['niveau'] = niveau
    # Récupérer les modules de la filière de l'étudiant
    cursor.execute("SELECT id_module, nom_module FROM module WHERE id_filiere=%s", (id_filiere,))
    modules = cursor.fetchall()
    
    notes_manquantes = []
    for module in modules:
        cursor.execute("""
            SELECT m.nom_module, ma.nom_matiere, COUNT(n.id_notematiere) as nb_notes
            FROM module m
            INNER JOIN matiere ma ON m.id_module = ma.id_module
            LEFT JOIN notematiere n ON ma.id_matiere = n.id_matiere AND n.id = %s
            WHERE m.id_module = %s
            GROUP BY m.nom_module, ma.nom_matiere
            HAVING COUNT(n.id_notematiere) = 0
        """, (id, module[0]))
        result = cursor.fetchall()
        if result:
            notes_manquantes.append(result)

    if notes_manquantes:
        return render_template('notes_manquantes.html', modules=notes_manquantes, etudiant=etudiant)

    else:
        # Insérer les notes de l'étudiant pour chaque module dans la table notemodule
        for module in modules:
            cursor.execute("""
                SELECT AVG(note_notematiere) 
                FROM matiere 
                JOIN notematiere ON matiere.id_matiere = notematiere.id_matiere 
                WHERE id_module=%s AND id=%s AND id_notematiere IN (
                SELECT MAX(id_notematiere)
                FROM notematiere
                WHERE id_matiere = matiere.id_matiere
                
            )
            """, (module[0], id))
            note = cursor.fetchone()[0]
            if note is not None:
                note = round(note, 2)
                cursor.execute("INSERT INTO notemodule (id_module, note_notemodule,id) VALUES (%s, %s,%s)", (module[0], note, id))
                g.db.commit()

        cursor.execute("""
            SELECT DISTINCT module.nom_module, notemodule.note_notemodule 
            FROM module 
            JOIN notemodule ON module.id_module = notemodule.id_module 
            WHERE notemodule.id=%s AND notemodule.id_notemodule IN (
                SELECT MAX(id_notemodule)
                FROM notemodule
                WHERE notemodule.id_module = module.id_module
                GROUP BY module.id_module
            )
            ORDER BY module.nom_module
        """, (id,))
        modules = cursor.fetchall()
    
        # Récupérer les notes de chaque module de l'étudiant à partir de la table notemodule 
        cursor.execute("""SELECT note_notemodule FROM notemodule WHERE id=%s AND notemodule.id_notemodule IN (
                SELECT MAX(id_notemodule)
                FROM notemodule
                GROUP BY notemodule.id_module
            )
            """, (id,))
        notes_modules = [note[0] for note in cursor.fetchall()]

        # Calculer la moyenne générale
        if len(notes_modules) > 0:
            moyenne_generale = round(sum(notes_modules) / len(notes_modules), 2)
        else:
            moyenne_generale = None
        
            
        cursor.execute("""
                SELECT notemodule.id_module
                FROM notemodule 
                JOIN (
                    SELECT id_module, MAX(id_notemodule) AS max_id_notemodule
                    FROM notemodule
                    GROUP BY id_module
                ) max_notemodule
                ON notemodule.id_module = max_notemodule.id_module AND notemodule.id_notemodule = max_notemodule.max_id_notemodule
                WHERE notemodule.id = %s
            """, (id,))
        mod = [mod[0] for mod in cursor.fetchall()]
        # Insérer les notes de chaque module de l'étudiant dans la table relevenote
        id_notemodule=None
        for module in mod:
            cursor.execute("""
                SELECT id_notemodule
                FROM notemodule 
                WHERE id = %s AND id_module = %s
                GROUP BY id_notemodule
            """, (id, module))
            result = cursor.fetchall()
            for result in result:
                if result is not None:
                    id_notemodule= result[0]
                    cursor.execute("""
                        INSERT INTO relevenote (id, id_module, id_notemodule)
                        VALUES (%s, %s, %s)
                    """, (id, module, id_notemodule))
                    
        # Enfin, commiter les changements
        g.db.commit()
        
        

        relevedenote=render_template('relevenote_admin2.html', modules=modules, etudiant=etudiant,moyenne_generale =moyenne_generale )
        filename=etudiant['nom']+"_"+etudiant['prenom']+"_"+etudiant['filiere']+"_Niveau"+str(etudiant['niveau'])
        filepath="PDFs/"+filename+".pdf"
        try:
            pdf =pdfkit.from_string(relevedenote, filepath, configuration = config)
        
        except:
            print("erreur!!")
            
        hashpdf=sha256sum(filepath)
        cursor.execute("UPDATE relevenote SET Hash = %s WHERE id=%s",( hashpdf,id))
        g.db.commit()
        g.db.close()                  
        return render_template('relevenote_admin1.html', modules=modules, etudiant=etudiant,moyenne_generale =moyenne_generale,hashpdf=hashpdf)

#//////////////////////////PROF/////////////////////////
@app.route('/accprof' , methods=['GET'])
def accprof():
    g.db = connect_db()  # Établir une connexion à la base de données
    cursor = g.db.cursor()

    mail = session.get('email')
    cursor.execute("SELECT id_prof, nom_prof, prenom_prof FROM professeur WHERE email_prof='" + mail + "'")
    record3 = cursor.fetchone() # Récupère le premier enregistrement de la requête exécutée précédemment
    professeur = {
        'id_prof': str(record3[0]),
        'nom_prof': record3[1],
        'prenom_prof': record3[2]
    }

    cursor.execute("SELECT f.nom_filiere FROM filiere f, professeur p, filiere_prof fp WHERE fp.id_prof=p.id_prof AND fp.id_filiere=f.id_filiere AND p.id_prof= '" + professeur['id_prof'] + "'")
    filieres = cursor.fetchall()
    g.db.close()  # Fermer la connexion à la base de données
    return render_template('accueil_prof.html', professeur=professeur, filieres=filieres)

@app.route('/semprof/<filiere>', methods=['GET'])
def semprof(filiere):
    # Utilisez la variable filiere dans votre requête SQL pour filtrer les résultats
    g.db = connect_db()  # Établir une connexion à la base de données
    cursor = g.db.cursor()
    mail = session.get('email')
    cursor.execute("SELECT id_prof FROM professeur WHERE email_prof='" + mail + "'")
    record3 = cursor.fetchone()#récupère le premier enregistrement de la requête exécutée précédemment
    profid=str(record3[0])
    cursor.execute("SELECT s.id_semestre FROM semestre s , semestre_filiere_prof sfp , filiere f WHERE s.id_semestre=sfp.id_semestre and sfp.id_filiere=f.id_filiere and sfp.id_prof = %s AND f.nom_filiere = %s", (profid,filiere,))   
    semestres = cursor.fetchall()
    for s in semestres:
        print(s)
    g.db.close()  # Fermer la connexion à la base de données
    return render_template('semestre_prof.html',filiere=filiere , semestres=semestres)

@app.route('/modules/<filiere>/<semestre>', methods=['GET'])
def modules(filiere, semestre):
    # Utilisez les variables filiere et semestre dans votre requête SQL pour filtrer les résultats
    g.db = connect_db()  # Établir une connexion à la base de données
    cursor = g.db.cursor()
    mail = session.get('email')
    cursor.execute("SELECT id_prof FROM professeur WHERE email_prof='" + mail + "'")
    record3 = cursor.fetchone()#récupère le premier enregistrement de la requête exécutée précédemment
    profid=str(record3[0])
    cursor.execute("SELECT m.nom_module from module m , module_prof mp , filiere f WHERE m.id_module=mp.id_module and f.id_filiere=m.id_filiere and mp.id_prof=%s and m.id_semestre=%s and f.nom_filiere=%s ",(profid,semestre,filiere,))
    modules = cursor.fetchall()
    for m in modules:
        print(m)
    g.db.close()  # Fermer la connexion à la base de données
    return render_template('module_prof.html',semestre=semestre , filiere=filiere , modules=modules)

@app.route('/matiereprof/<filiere>/<semestre>/<module>', methods=['GET'])
def matiereprof(filiere,semestre,module):
    # Utilisez la variable filiere dans votre requête SQL pour filtrer les résultats
    g.db = connect_db()  # Établir une connexion à la base de données
    cursor = g.db.cursor()
    mail = session.get('email')
    cursor.execute("SELECT id_prof FROM professeur WHERE email_prof='" + mail + "'")
    record3 = cursor.fetchone()#récupère le premier enregistrement de la requête exécutée précédemment
    profid=str(record3[0])
    cursor.execute("SELECT mt.nom_matiere FROM matiere mt , module m WHERE m.id_module=mt.id_module and m.nom_module=%s and mt.id_prof=%s  ",(module,profid,))
    matieres = cursor.fetchall()
    for s in matieres :
        print(s)
    g.db.close()  # Fermer la connexion à la base de données
    return render_template('matiere_prof.html',filiere=filiere,semestre=semestre,module=module,matieres=matieres)

@app.route('/ajouter_note', methods=['POST'])
def ajouter_note():
    g.db = connect_db()  # Établir une connexion à la base de données
    users = request.form.getlist('nom')  # Obtenir la liste des noms d'utilisateurs du formulaire
    prenoms = request.form.getlist('prenom')  # Obtenir la liste des prénoms d'utilisateurs du formulaire
    notes = request.form.getlist('note')  # Obtenir la liste des notes du formulaire
    matiere = request.form.get('matiere')  # Obtenir la matière du formulaire
    cursor = g.db.cursor()
    mat = None
    id_matiere = None
    if matiere:
        cursor.execute("SELECT id_matiere FROM matiere WHERE nom_matiere=%s", (matiere,))
        mat = cursor.fetchone()
    if mat:
        id_matiere = int(mat[0])

    if id_matiere is not None:
        # Parcourir les listes d'utilisateurs, prénoms et notes simultanément
        for i in range(len(users)):
            user = users[i]
            prenom = prenoms[i]
            note = notes[i]
            cursor.execute("SELECT id FROM user WHERE nom=%s AND prenom=%s", (user, prenom,))
            etud = cursor.fetchone()
            if etud:
                id_user = int(etud[0])
                # Vérifier si la note existe déjà dans la base de données
                cursor.execute("SELECT * FROM notematiere WHERE id_matiere=%s AND id=%s", (id_matiere, id_user,))
                note_existe = cursor.fetchone()
                if not note_existe:
                    # Insérer les données dans la table notematiere
                    cursor.execute("INSERT INTO notematiere (id_matiere, id, note_notematiere) VALUES (%s, %s, %s)", (id_matiere, id_user, note))
                else:
                    # Gérer le cas où la note existe déjà
                    return render_template('erreur.html', message="La note pour l'étudiant {} {} existe déjà.".format(user, prenom))
        g.db.commit()
        return render_template('confirmation.html', matiere=matiere)
    else:
        # Gérer le cas où la matière est manquante ou incorrecte
        return render_template('erreur.html', message="Matière manquante ou incorrecte.")  # Remplacer 'erreur.html' par le nom de votre vue...



@app.route('/liste_etud/<filiere>/<semestre>/<module>/<matiere>', methods=['GET'])
def liste_etud(filiere, semestre, module, matiere):
    g.db = connect_db()
    cursor = g.db.cursor()
    cursor.execute("SELECT u.id, u.nom, u.prenom, n.note_notematiere FROM user u LEFT JOIN notematiere n ON u.id = n.id AND n.id_matiere = (SELECT m.id_matiere FROM matiere m WHERE m.nom_matiere = %s) WHERE u.id_semestre = %s", (matiere, semestre))
    users = cursor.fetchall()
    g.db.close()
    
    return render_template('liste_etud.html', filiere=filiere, semestre=semestre, module=module, matiere=matiere, users=users)





@app.route('/login', methods=['GET', 'POST'])
def log():
    session.pop('logged_in', None)
    session.pop('profil', None)
    session.pop('name', None)
    return connectTo();


if __name__ == '__main__':
    app.run(debug=True)


