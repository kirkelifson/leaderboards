__author__ = 'gnaughton'

from sqlalchemy.exc import OperationalError, IntegrityError

from core.models import db, DBUser, DBScore, DBMap


try:
    print "Creating schema..."
    db.create_all()
    print "Committing schema..."
    db.session.commit()

##    print "Creating webmaster user"
##    user = DBUser(76561198011358548, access=11)
##    db.session.add(user)
##    db.session.commit()
##
##    print "Creating first map"
##    map = DBMap("bhop_monsterjam", "Monster Jam", 'http://cdn.momentum-mod.org/maps/bhop_monsterjam/bhop_monsterjam.bsp', 'http://cdn.akamai.steamstatic.com/steamcommunity/public/images/avatars/fe/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg', 2, 3, 1)
##
##    print "Creating first score"
##    score = DBScore(76561198011358548, 1, 3960, 66, "lololololololololol")
##
##    
##    db.session.add(map)
##    db.session.add(score)
##    db.session.commit()

    print "Successfully set up the DB."

except OperationalError as e:
    print "Error: Failed to provision database.\n" \
        "Did you edit core/__init__.py with your config values? \n" \
        "Exception: %s" % e

except IntegrityError as e:
    print "Error: There's already an admin user. \n" \
        "We can't add another one."
