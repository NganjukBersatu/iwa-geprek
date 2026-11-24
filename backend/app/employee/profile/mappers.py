"""Turns the profile into its response schema."""
from app.core.http import static_url
from app.employee.profile.domain import Profile
from app.employee.profile.schemas import ProfileOut


def profile_out(profile: Profile, base_url: str) -> ProfileOut:
    user = profile.user
    return ProfileOut(
        name=user.name,
        username=user.username,
        role_name=user.role.name if user.role else "-",
        outlet_name=profile.outlet_name,
        joined_date=user.joined_date,
        birth_date=user.birth_date,
        phone=user.phone,
        address=user.address,
        email=user.email,
        gender=user.gender,
        emergency_name=user.emergency_name,
        emergency_phone=user.emergency_phone,
        emergency_relation=user.emergency_relation,
        photo_url=static_url(base_url, user.photo_key),
    )
