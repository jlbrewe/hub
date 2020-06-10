import random

from django.conf import settings
from django.db.utils import IntegrityError

from accounts.models import Account, AccountRole, AccountTeam, AccountUser
from projects.models import Project
from users.models import User


def run(*args):
    """Create development database."""

    # Ensure that this is only used in development
    assert settings.DEBUG

    #################################################################
    # Users
    #################################################################

    # Admin (super user)
    admin = User.objects.create_user(
        username="admin",
        password="admin",
        first_name="Admin",
        email="admin@example.com",
    )
    admin.is_staff = True
    admin.is_superuser = True
    admin.save()

    # Staff member (not super user, but can access admin interface)
    staff = User.objects.create_user(
        username="staff",
        password="staff",
        first_name="Staff",
        email="staff@example.com",
    )
    staff.is_staff = True
    staff.save()

    for spec in [
        # Generic users that are added to EVERY account in these different roles
        ("member", "Member", "User"),
        ("manager", "Manager", "User"),
        ("owner", "Owner", "User"),
        # Example users
        ("amitabh", "Amitabh", "Modi"),
        ("anna", "Anna", "Andersson"),
        ("daniel", "Daniel", "Colreavy"),
        ("zahra", "Zahra", "Temitope"),
    ]:
        User.objects.create_user(
            username=spec[0],
            password=spec[0],
            first_name=spec[1],
            last_name=spec[2],
            email=spec[0] + "@example.com",
        )

    member = User.objects.get(username="member")
    manager = User.objects.get(username="manager")
    owner = User.objects.get(username="owner")

    # Add varying amounts of profile data for these example users

    amitabh = User.objects.get(username="amitabh").personal_account
    amitabh.location = "Sydney, Australia"
    amitabh.image.save("amitabh.png", open("scripts/data/amitabh.png", "rb"))

    anna = User.objects.get(username="anna").personal_account
    anna.display_name = "Dr Anna Andersson"
    anna.location = "Stockholm, Sweden"
    anna.website = "https://anna.example.edu/profile.html"
    anna.email = "anna@example.edu"
    anna.image.save("anna.png", open("scripts/data/anna.png", "rb"))

    daniel = User.objects.get(username="daniel").personal_account
    daniel.location = "Dublin"
    daniel.email = "daniel@example.edu"
    daniel.image.save("daniel.png", open("scripts/data/daniel.png", "rb"))

    zahra = User.objects.get(username="zahra").personal_account
    zahra.location = "Nairobi, Kenya, East Africa"
    zahra.website = "https://example.com"
    zahra.image.save("zahra.png", open("scripts/data/zahra.png", "rb"))

    #################################################################
    # Accounts
    #################################################################

    # A stencila account is needed as the default for running jobs etc

    # stencila = Account.objects.create(name="stencila")

    # Example organizations

    for name in ["biotech-corp", "hapuku-university", "pewsey-publishing"]:
        account = Account.objects.create(name=name)

        # Add their image
        account.image.save(
            "account-logo.png", open("scripts/data/{0}.png".format(name), "rb")
        )

        # The generic users have their roles on every account
        AccountUser.objects.create(
            account=account, user=member, role=AccountRole.MEMBER.name
        )
        AccountUser.objects.create(
            account=account, user=manager, role=AccountRole.MANAGER.name
        )
        AccountUser.objects.create(
            account=account, user=owner, role=AccountRole.OWNER.name
        )

        # In addition, some other randome users are added with random roles
        for user in random_users():
            try:
                AccountUser.objects.create(
                    account=account, user=user, role=random_account_role()
                )
            except IntegrityError:
                pass

        # Each account has a "first-team" team with the generic users, plus a random
        # number of random users
        team1 = AccountTeam.objects.create(account=account, name="first-team")
        team1.members.set([member, owner, manager] + random_users())

        # Each account has a random number of others teams each
        # with a random name and random number of random users
        # (who don't need to be be users of the organizations)
        for index in range(random.randint(1, 5)):
            team = AccountTeam.objects.create(account=account, name=random_team_name())
            team.members.set(random_users())

    biotech = Account.objects.get(name="biotech-corp")
    biotech.display_name = "Biotech Corporation"
    biotech.location = "Portland, USA"
    biotech.website = "https://biotech.example.com"
    biotech.email = "contact@biotech.example.com"
    biotech.save()

    hapuku = Account.objects.get(name="hapuku-university")
    hapuku.display_name = "Hapuku University"
    hapuku.location = "Hapuku, Kaikoura, New Zealand"
    hapuku.website = "https://hapuku.example.edu"
    hapuku.email = "contact@hapuku.example.edu"
    hapuku.save()

    pewsey = Account.objects.get(name="pewsey-publishing")
    pewsey.display_name = "Pewsey Publishing"
    pewsey.location = "UK"
    pewsey.website = "https://pewsey.example.com"
    pewsey.email = "contact@pewsey.example.com"
    pewsey.save()

    #################################################################
    # Projects
    #################################################################

    # Each account has one private and one public project

    for account in Account.objects.all():
        Project.objects.create(
            name="first-project",
            title="First project",
            account=account,
            creator=random_account_user(account),
            public=True,
            description="""
    A public project. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut la
    bore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex eacom
    modo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. E
    xcepteur sint occaecat cupidatat non roident, sunt in culpa qui officia deserunt mollit anim id est laborum.
            """.strip(),
        )

        Project.objects.create(
            name="second-project",
            title="Second project",
            account=account,
            creator=random_account_user(account),
            public=False,
            description="A private project.",
        )


def random_users(num=None):
    """Get a random set of users."""
    all = User.objects.order_by("?").all()
    if num is None:
        num = random.randint(1, len(all))
    return all[:num]


def random_account_user(account):
    """Get a random user for an account."""
    return AccountUser.objects.filter(account=account).order_by("?").first().user


def random_account_role():
    """Get a random account role."""
    return random.choice([e.name for e in AccountRole])


def random_team_name():
    """Get a random team name."""
    return random.choice(
        ["editors", "authors", "reviewers", "special-project-team", "vision-2020-team"]
    )
