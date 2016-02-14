__author__ = 'gnaughton'

from sqlalchemy.exc import OperationalError, IntegrityError

from core.models import db, DBUser, DBScore, DBMap


try:
    print "Creating schema..."
    db.create_all()
    print "Committing schema..."
    db.session.commit()

    #We don't create it because we just don't need it (yet)
    print "Creating webmaster user"
    user = DBUser(3123123, access=11)
    db.session.add(user)
    db.session.commit()

    print "Creating first score"
    score = DBScore("76561198030388441", "bhop_monsterjam", 3960, 66, "lololololololololol")

    print "Creating first map"
    map = DBMap("bhop_monsterjam", "Monster Jam", 2, 3, 1)

    db.session.add(map)
    db.session.add(score)
    db.session.commit()

    print "Successfully set up the DB."

except OperationalError as e:
    print "Error: Failed to provision database.\n" \
        "Did you edit core/__init__.py with your config values? \n" \
        "Exception: %s" % e

except IntegrityError as e:
    print "Error: There's already an admin user. \n" \
        "We can't add another one."
