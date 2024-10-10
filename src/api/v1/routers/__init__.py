from .auth import router as auth
from .benefit import router as benefit
from .category import router as category
from .legalentity import router as legalentity
from .position import router as position
from .request import router as request
from .users import router as users
from .users_fake import router as users_fake

list_of_routers = [
    auth,
    benefit,
    category,
    legalentity,
    position,
    request,
    users_fake,
    users,
]
