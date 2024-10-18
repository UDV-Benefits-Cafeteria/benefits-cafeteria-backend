from sqlalchemy import Column, DateTime, MetaData, text
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models with default metadata and timestamp columns.

    This class defines a base model that other models can inherit from. It sets up
    metadata with a naming convention for primary keys, foreign keys, indexes,
    unique constraints, and check constraints. Additionally, it provides automatic
    `created_at` and `updated_at` columns with UTC timestamps.

    Attributes:
        repr_cols_num (int): The default number of columns to display in the `__repr__` output.
        repr_cols (tuple): A tuple of specific column names to include in the `__repr__` output.
    """

    metadata = MetaData(
        naming_convention={
            "pk": "pk_%(table_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
        }
    )

    @declared_attr
    def created_at(cls):
        """
        The UTC timestamp when a record is created.

        This column is automatically populated with the current UTC time
        when a record is inserted.

        :return: A DateTime column with timezone support.
        """
        return Column(
            DateTime(timezone=True),
            server_default=text("TIMEZONE('utc', NOW())"),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):
        """
        The UTC timestamp when a record is last updated.

        This column is automatically updated with the current UTC time whenever
        the record is modified.

        :return: A DateTime column with timezone support.
        """
        return Column(
            DateTime(timezone=True),
            server_default=text("TIMEZONE('utc', NOW())"),
            onupdate=text("TIMEZONE('utc', NOW())"),
            nullable=False,
        )

    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self) -> str:
        """
        Generate a string representation of the model instance.

        The representation includes a subset of the model's columns. By default,
        it displays the first three columns or the columns specified in `repr_cols`.

        :return: A string representation of the model instance.
        :rtype: str
        """
        column_names = list(self.__table__.columns.keys())
        cols = []

        for idx, col_name in enumerate(column_names):
            if col_name in self.repr_cols or idx < self.repr_cols_num:
                value = getattr(self, col_name)
                cols.append(f"{col_name}={repr(value)}")

        cols_str = ", ".join(cols)
        return f"<{self.__class__.__name__}({cols_str})>"
