from app.employee.performance.rating.domain import Rating
from app.employee.performance.rating.schemas import ComponentOut, RatingGroupOut, RatingOut


def rating_out(rating: Rating) -> RatingOut:
    return RatingOut(
        stars=rating.stars,
        score=rating.score,
        groups=[
            RatingGroupOut(
                key=group.key,
                score=group.score,
                components=[ComponentOut(**vars(component)) for component in group.components],
            )
            for group in rating.groups
        ],
    )
