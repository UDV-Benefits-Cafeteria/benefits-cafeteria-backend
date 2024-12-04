import datetime


def prepare_entities_for_export(entities):
    for entity in entities:
        # Preventing error: 'Excel does not support datetimes with timezones. Please ensure that datetimes are timezone unaware before writing to Excel.'
        if isinstance(entity.created_at, datetime.datetime):
            entity.created_at = entity.created_at.replace(tzinfo=None)
            # Make created_at time correspond with the database value (in UTC)
            entity.created_at += datetime.timedelta(hours=5)

        if isinstance(entity.updated_at, datetime.datetime):
            entity.updated_at = entity.updated_at.replace(tzinfo=None)
            entity.updated_at += datetime.timedelta(hours=5)

    return entities
