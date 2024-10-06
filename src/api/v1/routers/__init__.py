from .benefit import router as benefit
from .category import router as category
from .legalentity import router as legalentity
from .position import router as position
from .request import router as request
from .users import router as user
from .auth import router as auth

list_of_routers = [benefit, request, user, category, position, legalentity, auth]
