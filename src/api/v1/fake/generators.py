import random
from datetime import datetime, timedelta
from decimal import Decimal

from faker import Faker

from src.schemas.benefit import BenefitImageRead, BenefitRead
from src.schemas.category import CategoryRead
from src.schemas.legalentity import LegalEntityRead
from src.schemas.position import PositionRead
from src.schemas.request import BenefitRequestRead, BenefitStatus
from src.schemas.user import UserRead, UserRole

fake = Faker("ru_RU")


def generate_fake_benefit(benefit_id: int) -> BenefitRead:
    name = fake.sentence(nb_words=4)
    description = fake.text(max_nb_chars=200)
    real_currency_cost = round(random.uniform(100, 10000), 2)
    amount = random.randint(1, 100)
    usage_limit = random.randint(1, 100)
    usage_period_days = random.randint(1, 365)
    period_start_date = datetime.now()
    available_from = datetime.now()
    available_by = datetime.now() + timedelta(days=random.randint(1, 365))
    coins_cost = random.randint(100, 1000)
    min_level_cost = random.randint(1, 10)
    adaptation_required = random.choice([True, False])

    images = [
        BenefitImageRead(
            id=i + random.randint(1000, 9999),
            benefit_id=benefit_id,
            image_url=fake.image_url(),
            is_primary=(i == 1),
            description=fake.sentence(nb_words=5),
        )
        for i in range(1, 4)
    ]

    category = CategoryRead(id=random.randint(1, 100), name=fake.word())
    if random.choice([True, False]):
        positions = [PositionRead(id=i, name=fake.job()) for i in range(1, 4)]
    else:
        positions = []

    benefit = BenefitRead(
        id=benefit_id,
        name=name,
        category_id=category.id,
        category=category,
        is_active=True,
        description=description,
        real_currency_cost=Decimal(str(real_currency_cost)),
        amount=amount,
        is_fixed_period=False,
        usage_limit=usage_limit,
        usage_period_days=usage_period_days,
        period_start_date=period_start_date,
        available_from=available_from,
        available_by=available_by,
        coins_cost=coins_cost,
        min_level_cost=min_level_cost,
        adaptation_required=adaptation_required,
        images=images,
        positions=positions,
    )

    return benefit


def generate_fake_benefit_request(
    request_id: int, user_id: int = None
) -> BenefitRequestRead:
    benefit_id = random.randint(1, 100)
    if not user_id:
        user_id = random.randint(1, 100)
    status = random.choice(list(BenefitStatus))
    content = fake.text(max_nb_chars=200)
    comment = fake.sentence()

    benefit = generate_fake_benefit(benefit_id)
    user = generate_fake_user(user_id)

    benefit_request = BenefitRequestRead(
        id=request_id,
        benefit_id=benefit_id,
        user_id=user_id,
        status=status,
        content=content,
        comment=comment,
        benefit=benefit,
        user=user,
    )

    return benefit_request


def generate_fake_position(position_id: int) -> PositionRead:
    name = fake.job()
    position = PositionRead(id=position_id, name=name)
    return position


def generate_fake_legal_entity(entity_id: int) -> LegalEntityRead:
    name = fake.company()
    legal_entity = LegalEntityRead(id=entity_id, name=name)
    return legal_entity


def generate_fake_user(user_id: int) -> UserRead:
    position_id = random.randint(1, 100)
    position = generate_fake_position(position_id)

    legal_entity_id = random.randint(1, 100)
    legal_entity = generate_fake_legal_entity(legal_entity_id)

    hired_at = fake.date_between(start_date="-5y", end_date="today")

    role = random.choice(list(UserRole))

    user = UserRead(
        id=user_id,
        email=fake.email(),
        firstname=fake.first_name(),
        lastname=fake.last_name(),
        middlename=fake.middle_name() if random.choice([True, False]) else None,
        position_id=position_id,
        legal_entity_id=legal_entity_id,
        position=position,
        legal_entity=legal_entity,
        role=role,
        hired_at=hired_at,
        is_active=True,
        is_adapted=random.choice([True, False]),
        is_verified=random.choice([True, False]),
        coins=random.randint(0, 1000),
    )

    return user
