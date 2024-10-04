from faker import Faker

from datetime import datetime, timedelta
from decimal import Decimal
import random

from src.schemas.benefit import BenefitRead, BenefitImageRead
from src.schemas.category import CategoryRead
from src.schemas.position import PositionRead

fake = Faker('ru_RU')

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
            description=fake.sentence(nb_words=5)
        ) for i in range(1, 4)
    ]

    category = CategoryRead(
        id=random.randint(1, 100),
        name=fake.word()
    )
    if random.choice([True, False]):
        positions = [
            PositionRead(
                id=i,
                name=fake.job()
            ) for i in range(1, 4)
        ]
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
        positions=positions
    )

    return benefit

