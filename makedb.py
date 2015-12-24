__author__ = 'gnaughton'

from sqlalchemy.exc import OperationalError, IntegrityError

from core.models import db, DBUser, DBScore


try:
    print "Creating schema..."
    db.create_all()
    print "Committing schema..."
    db.session.commit()

    print "Creating admin user"
    user = DBUser('admin', 'admin@admin.com', 'admin', access=10)
    db.session.add(user)
    db.session.commit()

    print "Creating first score"
    score = DBScore("STEAM_0:1:35061356", "bhop_monsterjam", 3960, "lololololololololol")

    db.session.add(score)
    db.session.commit()

    print "Successfully set up the DB. Log in with admin:admin"
    print "Be sure to change your password."

except OperationalError as e:
    print "Error: Failed to provision database.\n" \
        "Did you edit core/__init__.py with your config values? \n" \
        "Exception: %s" % e

except IntegrityError as e:
    print "Error: There's already an admin user. \n" \
        "We can't add another one."