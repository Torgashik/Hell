from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from your_models import db, Sinner, Demon, Course, CourseSinner

sqlite_engine = create_engine('sqlite:///your_sqlite_db.db')
sqlite_session = sessionmaker(bind=sqlite_engine)()

mysql_engine = create_engine('mysql+pymysql://username:password@localhost/your_mysql_db')
mysql_session = sessionmaker(bind=mysql_engine)()

Base = declarative_base()
Base.metadata.create_all(mysql_engine)

def migrate_data():
    sinners = sqlite_session.query(Sinner).all()
    for sinner in sinners:
        mysql_session.add(Sinner(
            id=sinner.id,
            username=sinner.username,
            password=sinner.password,
            role=sinner.role,
            first_name=sinner.first_name,
            last_name=sinner.last_name,
            middle_name=sinner.middle_name,
            age=sinner.age,
            gender=sinner.gender,
            registration_date=sinner.registration_date,
            profile_photo=sinner.profile_photo,
            sins=sinner.sins
        ))

    demons = sqlite_session.query(Demon).all()
    for demon in demons:
        mysql_session.add(Demon(
            id=demon.id,
            username=demon.username,
            password=demon.password,
            role=demon.role,
            first_name=demon.first_name,
            profile_photo=demon.profile_photo,
            sin=demon.sin
        ))

    courses = sqlite_session.query(Course).all()
    for course in courses:
        mysql_session.add(Course(
            id=course.id,
            title=course.title,
            description=course.description,
            demon_id=course.demon_id,
            demon_name=course.demon_name,
            creation_date=course.creation_date
        ))

    course_sinners = sqlite_session.query(CourseSinner).all()
    for cs in course_sinners:
        mysql_session.add(CourseSinner(
            course_id=cs.course_id,
            sinner_id=cs.sinner_id
        ))

    mysql_session.commit()
    
try:
    migrate_data()
    print("Миграция завершена успешно!")
except Exception as e:
    print(f"Ошибка миграции: {e}")
    mysql_session.rollback()
finally:
    sqlite_session.close()
    mysql_session.close()
