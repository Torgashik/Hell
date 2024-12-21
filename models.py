from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def formate_date(date):
    date = date.strftime('%d.%m.%Y')
    return date

# Модель для грешников (пользователей)
class Sinner(db.Model):
    __tablename__ = 'sinners'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Уникальный ID
    username = db.Column(db.String(50), unique=True, nullable=False)  # Логин
    password = db.Column(db.String(255), nullable=False)  # Пароль
    role = db.Column(db.String(20), default='грешная душа', nullable=False)  # Роль
    first_name = db.Column(db.String(20), nullable=True, default=None)  # Имя
    last_name = db.Column(db.String(20), nullable=True, default=None)  # Фамилия
    middle_name = db.Column(db.String(20), nullable=True, default=None)  # Отчество
    age = db.Column(db.Integer, nullable=True, default=None)  # Возраст
    gender = db.Column(db.String(20), nullable=True, default=None)  # Пол
    registration_date = db.Column(db.String(20), default=formate_date(datetime.utcnow()), nullable=False)  # Дата регистрации
    profile_photo = db.Column(db.LargeBinary, nullable=True, default=None) # Фото профиля
    sins = db.Column(db.String, nullable=True, default=None)  # Список грехов

    def __repr__(self):
        return f"<Sinner {self.id} - {self.username}>"
    

# Модель для демонов (админов)
class Demon(db.Model):
    __tablename__ = 'demons'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Уникальный ID
    username = db.Column(db.String(50), unique=True, nullable=False)  # Логин
    password = db.Column(db.String(255), nullable=False)  # Пароль
    role = db.Column(db.String(20), default='демон')  # Роль
    first_name = db.Column(db.String(20), nullable=False)  # Имя
    profile_photo = db.Column(db.LargeBinary, nullable=True, default=None)  # Путь к фото профиля
    sin = db.Column(db.String(50), nullable=False)  # Грех

    def __repr__(self):
        return f"<Demon {self.id} - {self.username}>"
    

# Модель для курсов
class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True) # Уникальный ID
    title = db.Column(db.String(100), nullable=False) #Название
    description = db.Column(db.Text, nullable=False) #Описание
    demon_id = db.Column(db.Integer, db.ForeignKey('demons.id')) #ID демона отвественного за курс
    demon_name = db.Column(db.String(100), nullable=False) #Имя демона
    creation_date = db.Column(db.String(20), default=formate_date(datetime.utcnow())) #Дата создания

    sinners = db.relationship('Sinner', secondary='course_sinners', backref='courses')

    def __repr__(self):
        return f"<Course {self.id} - {self.title}>"

# Связующая таблица 
class CourseSinner(db.Model):
    __tablename__ = 'course_sinners'

    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), primary_key=True)
    sinner_id = db.Column(db.Integer, db.ForeignKey('sinners.id'), primary_key=True)

    def __repr__(self):
        return f"<CourseSinner course_id={self.course_id} sinner_id={self.sinner_id}>"