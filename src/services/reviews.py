from typing import Optional

import src.repositories.exceptions as repo_exceptions
import src.schemas.user as user_schemas
import src.services.exceptions as service_exceptions
from src.db.db import async_session_factory, get_transaction_session
from src.logger import service_logger
from src.repositories.benefits import BenefitsRepository
from src.repositories.reviews import ReviewsRepository
from src.repositories.users import UsersRepository
from src.schemas import review as schemas
from src.services.base import BaseService


class ReviewsService(
    BaseService[schemas.ReviewCreate, schemas.ReviewRead, schemas.ReviewUpdate]
):
    repo = ReviewsRepository()
    users_repo: UsersRepository = UsersRepository()
    benefits_repo: BenefitsRepository = BenefitsRepository()
    create_schema = schemas.ReviewCreate
    read_schema = schemas.ReviewRead
    update_schema = schemas.ReviewUpdate

    async def create(
        self,
        create_schema: schemas.ReviewCreate,
        current_user: user_schemas.UserRead = None,
    ) -> schemas.ReviewRead:
        service_logger.info(f"Creating review for user_id: {current_user.id}")

        request_data = create_schema.model_dump(exclude_unset=True)
        request_data["user_id"] = current_user.id

        async with get_transaction_session() as session:
            try:
                benefit = await self.benefits_repo.read_by_id(
                    session, create_schema.benefit_id
                )
                if benefit is None:
                    service_logger.warning(
                        f"Benefit with ID {create_schema.benefit_id} not found"
                    )
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__,
                        f"benefit_id: {create_schema.benefit_id}",
                    )

                user = await self.users_repo.read_by_id(
                    session, request_data["user_id"]
                )
                if user is None:
                    service_logger.warning(
                        f"User with ID {request_data['user_id']} not found"
                    )
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__,
                        f"user_id: {request_data['user_id']}",
                    )

                created_review = await self.repo.create(session, request_data)

            except repo_exceptions.RepositoryError as e:
                service_logger.error(
                    f"Error creating {self.create_schema.__name__}: {str(e)}"
                )
                raise service_exceptions.EntityCreateError(
                    self.create_schema.__name__, str(e)
                )

        service_logger.info(
            "Review created successfully",
            extra={"review_id": created_review.id},
        )
        return self.read_schema.model_validate(created_review)

    async def update_by_id(
        self,
        entity_id: int,
        update_schema: schemas.ReviewUpdate,
        current_user: user_schemas.UserRead = None,
    ) -> Optional[schemas.ReviewRead]:
        service_logger.info(
            f"Updating {self.update_schema.__name__} with ID: {entity_id}"
        )

        async with get_transaction_session() as session:
            try:
                existing_review = await self.repo.read_by_id(session, entity_id)
                if not existing_review:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id: {entity_id}"
                    )

                if current_user.role == user_schemas.UserRole.EMPLOYEE:
                    if existing_review.user_id != current_user.id:
                        raise service_exceptions.EntityUpdateError(
                            self.read_schema.__name__,
                            "You do not have permission to update this review.",
                        )

                is_updated: bool = await self.repo.update_by_id(
                    session,
                    entity_id,
                    update_schema.model_dump(exclude_unset=True),
                )
                if not is_updated:
                    raise service_exceptions.EntityNotFoundError(
                        self.read_schema.__name__, f"entity_id: {entity_id}"
                    )

                entity = await self.repo.read_by_id(session, entity_id)

            except service_exceptions.EntityNotFoundError as e:
                service_logger.error(
                    f"Error updating entity with ID {entity_id}: {str(e)}"
                )
                raise
            except Exception as e:
                service_logger.error(
                    f"Unexpected error updating entity with ID {entity_id}: {str(e)}"
                )
                raise service_exceptions.EntityUpdateError(
                    self.__class__.__name__, str(e)
                )

        service_logger.info(
            f"Successfully updated {self.update_schema.__name__} with ID {entity_id}."
        )

        return self.read_schema.model_validate(entity)

    async def delete_by_id(
        self, entity_id: int, current_user: user_schemas.UserRead = None
    ) -> bool:
        service_logger.info(
            f"Deleting {self.read_schema.__name__} with ID: {entity_id}"
        )

        async with get_transaction_session() as session:
            try:
                existing_request = await self.repo.read_by_id(session, entity_id)
                if not existing_request:
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__, f"entity_id {entity_id}"
                    )

                if current_user.role == user_schemas.UserRole.EMPLOYEE:
                    if existing_request.user_id != current_user.id:
                        raise service_exceptions.EntityDeleteError(
                            self.read_schema.__name__,
                            "You do not have permission to delete this review.",
                        )

                is_deleted = await self.repo.delete_by_id(session, entity_id=entity_id)
            except service_exceptions.EntityNotFoundError as e:
                service_logger.error(
                    f"Error deleting review with ID {entity_id}: {str(e)}"
                )
                raise
            except Exception as e:
                service_logger.error(
                    f"Unexpected error deleting review with ID {entity_id}: {str(e)}"
                )
                raise service_exceptions.EntityDeleteError(
                    self.__class__.__name__, str(e)
                )

        if not is_deleted:
            service_logger.error(f"Review with ID {entity_id} not found for deletion.")
            raise service_exceptions.EntityNotFoundError(
                self.__class__.__name__, f"entity_id {entity_id}"
            )

        service_logger.info(f"Successfully deleted review with ID {entity_id}.")
        return is_deleted

    async def get_reviews_by_benefit_id(
        self,
        benefit_id: int,
        page: int = 1,
        limit: int = 10,
    ) -> list[schemas.ReviewRead]:
        service_logger.info(
            f"Retrieving reviews for Benefit ID {benefit_id}. Page: {page}, Limit: {limit}"
        )

        async with async_session_factory() as session:
            try:
                benefit = await self.benefits_repo.read_by_id(session, benefit_id)
                if not benefit:
                    service_logger.warning(f"Benefit with ID {benefit_id} not found.")
                    raise service_exceptions.EntityNotFoundError(
                        self.__class__.__name__,
                        f"Benefit with ID {benefit_id} does not exist.",
                    )

                reviews = await self.repo.read_by_benefit_id(
                    session=session, benefit_id=benefit_id, page=page, limit=limit
                )
            except service_exceptions.EntityNotFoundError:
                raise
            except Exception as e:
                service_logger.error(f"Unexpected error: {e}")
                raise service_exceptions.EntityReadError(
                    self.__class__.__name__, str(e)
                )

            validated_reviews = [
                self.read_schema.model_validate(review) for review in reviews
            ]

        service_logger.info(
            f"Successfully retrieved {len(validated_reviews)} reviews for Benefit ID {benefit_id}."
        )
        return validated_reviews
