from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from models import db, Sinner, Demon, Course, CourseSinner
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
import json
import base64

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "super_secret_key"

db.init_app(app)


# Начальная страница (auth.html)
@app.route('/')
def auth():
    return render_template('auth.html')

@app.template_filter('fromjson')
def fromjson_filter(value):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    
# Добавляем фильтр для обработки JSON
@app.template_filter('json_decode')
def json_decode_filter(value):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return []

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Неверный логин или пароль!")
            return redirect(url_for('register'))

        if len(username) < 8:
            flash("Логин должен быть не короче 8 символов!")
            return redirect(url_for('register'))
        if len(password) < 8:
            flash("Пароль должен быть не короче 8 символов!")
            return redirect(url_for('register'))

        existing_user = Sinner.query.filter_by(username=username).first()
        if existing_user:
            flash("Такой пользователь уже существует!")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = Sinner(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('reg.html')

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = Sinner.query.filter_by(username=username).first()

        if not user:
            user = Demon.query.filter_by(username=username).first()

        print(f"Ищем пользователя {username}, найден: {user is not None}")

        if user and check_password_hash(user.password, password):
            session['username'] = username

            if isinstance(user, Demon):
                session['demon_id'] = user.id

            if isinstance(user, Sinner) and any(v is None for v in [user.first_name, user.last_name, user.middle_name, user.age, user.gender, user.profile_photo]):
                return redirect(url_for('makeprofile', username=username))

            return redirect(url_for('index'))

        else:
            flash("Пользователь не найден или неверный пароль!")
            return redirect(url_for('login'))

    return render_template('login.html')

# Страница заполнения профиля
@app.route('/makeprofile/<username>', methods=['GET', 'POST'])
def makeprofile(username):
    user = Sinner.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        age = request.form['age']
        gender = request.form['gender']
        sins = request.form.getlist('sins')

        sins_json = json.dumps(sins)

        profile_photo = request.files['profile_photo']
        photo_data = profile_photo.read() if profile_photo else None

        user.first_name = first_name
        user.last_name = last_name
        user.middle_name = middle_name
        user.age = age
        user.gender = gender
        user.sins = sins_json
        user.profile_photo = photo_data
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('makeprofile.html', user=user)


# Главная страница
@app.route('/index')
def index():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = Sinner.query.filter_by(username=username).first() or Demon.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('login'))

    if isinstance(user, Sinner):
        courses_query = Course.query.filter(Course.sinners.any(id=user.id))
    else:
        courses_query = Course.query.filter_by(demon_id=user.id)

    page = request.args.get('page', 1, type=int)
    courses = courses_query.paginate(page=page, per_page=8, error_out=False)

    photo_base64 = None
    if user.profile_photo:
        photo_base64 = base64.b64encode(user.profile_photo).decode()

    return render_template('index.html', user=user, photo_base64=photo_base64, courses=courses)

# Страница курса
@app.route('/course/<int:course_id>')
def course_page(course_id):
    course = Course.query.get(course_id)
    if not course:
        return redirect(url_for('index'))

    return render_template('course_page.html', course=course)


# Страница профиля
@app.route('/profile/<username>')
def profile(username):
    user = Sinner.query.filter_by(username=username).first() or Demon.query.filter_by(username=username).first()

    if not user:
        return redirect(url_for('index'))

    photo_base64 = None
    if user.profile_photo:
        photo_base64 = base64.b64encode(user.profile_photo).decode()

    return render_template('profile.html', user=user, photo_base64=photo_base64)

# Страница редактирования профиля
@app.route('/editprofile/<username>', methods=['GET', 'POST'])
def editprofile(username):
    user = Sinner.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        age = request.form['age']
        password = request.form['password']

        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.middle_name = middle_name or user.middle_name
        user.age = age or user.age

        if password:
            user.password = generate_password_hash(password)

        if 'profile_photo' in request.files:
            profile_photo = request.files['profile_photo']
            if profile_photo:
                user.profile_photo = profile_photo.read()

        db.session.commit()
        return redirect(url_for('profile', username=user.username))

    return render_template('editprofile.html', user=user)

def get_image_binary(image_path):
    with open(image_path, "rb") as img_file:
        return img_file.read()

def create_test_demons():
    test_demons = [
        {"username": "Lucifer", "password": "password123", "first_name": "Люцифер", "sin": "Гордыня", "role": "старший демон", "profile_photo_path": "static/uploads/lucifer.jpg"},
        {"username": "Mammon", "password": "password123", "first_name": "Маммон", "sin": "Жадность", "role": "старший демон", "profile_photo_path": "static/uploads/mammon.jpg"},
        {"username": "Satan", "password": "password123", "first_name": "Сатана", "sin": "Гнев", "role": "старший демон", "profile_photo_path": "static/uploads/satan.jpg"},
        {"username": "Asmodeus", "password": "password123", "first_name": "Асмодей", "sin": "Похоть", "role": "старший демон", "profile_photo_path": "static/uploads/asmodeus.jpg"},
        {"username": "Beelzebub", "password": "password123", "first_name": "Вельзевул", "sin": "Черевоугодие", "role": "старший демон", "profile_photo_path": "static/uploads/beelzebub.jpg"},
        {"username": "Leviathan", "password": "password123", "first_name": "Левиафан", "sin": "Зависть", "role": "старший демон", "profile_photo_path": "static/uploads/leviathan.jpg"},
        {"username": "Belphegor", "password": "password123", "first_name": "Бельфегор", "sin": "Уныние", "role": "старший демон", "profile_photo_path": "static/uploads/belphegor.jpg"},
        {"username": "Devil", "password": "password666", "first_name": "Дьявол", "sin": "Дьяволопоклонничество", "role": "Босс", "profile_photo_path": "static/uploads/devil.jpg"},
    ]
    
    for demon_data in test_demons:
        existing_demon = Demon.query.filter_by(username=demon_data["username"]).first()
        if not existing_demon:
            hashed_password = generate_password_hash(demon_data["password"])
            profile_photo_binary = get_image_binary(demon_data["profile_photo_path"])
            new_demon = Demon(
                username=demon_data["username"],
                password=hashed_password,
                first_name=demon_data["first_name"],
                sin=demon_data["sin"],
                role=demon_data["role"],
                profile_photo=profile_photo_binary,
            )
            db.session.add(new_demon)
            db.session.commit()
    
# Функция выхода
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth'))

# Страница админ панели
@app.route('/admin_panel')
def admin_panel():
    username = session.get('username')
    demon_id = session.get('demon_id')

    if not username:
        return redirect(url_for('login'))

    user = Demon.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for('index'))

    sort_order = request.args.get('sort', 'alphabet_asc')

    if sort_order == 'alphabet_asc':
        courses = Course.query.order_by(Course.title.asc()).all()
    elif sort_order == 'alphabet_desc':
        courses = Course.query.order_by(Course.title.desc()).all()
    elif sort_order == 'sinners_asc':
        courses = Course.query.join(Course.sinners).group_by(Course.id).order_by(func.count(func.distinct(Course.sinners)).asc()).all()
    elif sort_order == 'sinners_desc':
        courses = Course.query.join(Course.sinners).group_by(Course.id).order_by(func.count(func.distinct(Course.sinners)).desc()).all()
    else:
        courses = Course.query.all()

    sinners = []
    demons = Demon.query.all()

    if user.username == 'Devil':
        sinners = Sinner.query.all()
    else:
        all_sinners = Sinner.query.all()

        for sinner in all_sinners:
            try:
                sins_list = json.loads(sinner.sins)
                if user.sin in sins_list:
                    sinners.append(sinner)
            except (TypeError, json.JSONDecodeError):
                continue

    return render_template('adminpanel.html', user=user, sinners=sinners, demons=demons, courses=courses, sort_order=sort_order)

# Функция удаления грешника
@app.route('/delete_sinner/<int:sinner_id>', methods=['GET', 'POST'])
def delete_sinner(sinner_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    sinner = Sinner.query.get(sinner_id)
    if sinner:
        db.session.delete(sinner)
    else:
        flash("")
    return redirect(url_for('admin_panel'))

# Функция удаления демона
@app.route('/delete_demon/<int:demon_id>', methods=['GET', 'POST'])
def delete_demon(demon_id):
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    user = Demon.query.filter_by(username=username).first()
    if not user or user.username != 'Devil':
        return redirect(url_for('index'))

    demon = Demon.query.get(demon_id)
    if demon:
        db.session.delete(demon)
        db.session.commit()
    else:
        flash("")
    return redirect(url_for('admin_panel'))

# Функция создания курса
@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    demon_id = session.get('demon_id')
    if not demon_id:
        return redirect(url_for('login'))

    demon = Demon.query.get(demon_id)
    if not demon:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        demon_name = demon.first_name

        new_course = Course(
            title=title,
            description=description,
            demon_id=demon.id,
            demon_name=demon_name
        )
        db.session.add(new_course)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('createcourse.html', demon=demon)

# Функция удаления курса
@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    demon_id = session.get('demon_id')
    if not demon_id:
        return redirect(url_for('login'))

    course = Course.query.get(course_id)
    if not course:
        return redirect(url_for('index'))

    demon = Demon.query.get(demon_id)
    if demon.username != 'Devil' and course.demon_id != demon_id:
        return redirect(url_for('index'))

    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('index'))

# Функция добавления грешника
@app.route('/add_sinner/<int:course_id>', methods=['POST'])
def add_sinner(course_id):
    sinner_id = request.form['sinner_id']
    
    existing_entry = CourseSinner.query.filter_by(course_id=course_id, sinner_id=sinner_id).first()
    
    if existing_entry:
        return redirect(url_for('admin_panel'))
    
    new_entry = CourseSinner(course_id=course_id, sinner_id=sinner_id)
    db.session.add(new_entry)
    db.session.commit()
    
    return redirect(url_for('admin_panel'))

@app.route('/remove_sinner/<int:course_id>', methods=['POST'])
def remove_sinner(course_id):
    sinner_id = request.form['sinner_id']
    entry = CourseSinner.query.filter_by(course_id=course_id, sinner_id=sinner_id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/add_sinner_modal/<int:course_id>', methods=['GET'])
def add_sinner_modal(course_id):
    sinners = Sinner.query.all()
    
    existing_sinners = db.session.query(CourseSinner.sinner_id).filter_by(course_id=course_id).all()
    existing_sinner_ids = [sinner.sinner_id for sinner in existing_sinners]
    
    available_sinners = [sinner for sinner in sinners if sinner.id not in existing_sinner_ids]
    
    return render_template('your_template.html', course_id=course_id, sinners=available_sinners)


@app.route('/add_all_sinners/<int:course_id>', methods=['POST'])
def add_all_sinners(course_id):
    course = Course.query.get(course_id)  # Получаем курс по ID
    if not course:
        return "Курс не найден", 404
    
    demon = Demon.query.get(course.demon_id)
    if not demon:
        return "Демон для курса не найден", 404

    demon_sin = demon.sin

    sinners = Sinner.query.all()
    for sinner in sinners:
        if sinner.sins:
            sinner_sins = json.loads(sinner.sins)
            if demon_sin in sinner_sins:
                if not CourseSinner.query.filter_by(course_id=course_id, sinner_id=sinner.id).first():
                    db.session.add(CourseSinner(course_id=course_id, sinner_id=sinner.id))

    db.session.commit()
    return redirect(url_for('admin_panel'))

# Инициализация базы данных
with app.app_context():
    db.create_all()
    create_test_demons()

if __name__ == '__main__':
    app.run(debug=True)
