import os
import django
import random
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartDesk.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Department, Project, Event, News, EmployeeProfile

def create_users(num_users):
    users = []
    for i in range(num_users):
        username = f"user{i+1}"
        email = f"user{i+1}@example.com"
        user = User.objects.create_user(username=username, email=email, password="password123")
        users.append(user)
    return users

def create_departments():
    departments = [
        Department.objects.create(name="Engineering", description="Software development and IT operations"),
        Department.objects.create(name="Marketing", description="Brand management and customer acquisition"),
        Department.objects.create(name="HR", description="Human resources and employee management"),
        Department.objects.create(name="Finance", description="Financial planning and accounting")
    ]
    return departments

def create_projects(users):
    projects = []
    for i in range(10):
        start_date = datetime.now().date() - timedelta(days=random.randint(0, 365))
        end_date = start_date + timedelta(days=random.randint(30, 180))
        project = Project.objects.create(
            name=f"Project {i+1}",
            description=f"Description for Project {i+1}",
            start_date=start_date,
            end_date=end_date,
            manager=random.choice(users)
        )
        team_members = random.sample(users, k=random.randint(2, 5))
        project.team_members.set(team_members)
        projects.append(project)
    return projects

def create_events():
    events = []
    for i in range(5):
        event_date = datetime.now() + timedelta(days=random.randint(1, 30))
        event = Event.objects.create(
            title=f"Event {i+1}",
            description=f"Description for Event {i+1}",
            date=event_date
        )
        events.append(event)
    return events

def create_news():
    news_items = []
    for i in range(8):
        news = News.objects.create(
            title=f"News Article {i+1}",
            content=f"Content for News Article {i+1}",
            date_published=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        news_items.append(news)
    return news_items

def create_employee_profiles(users, departments):
    for user in users:
        EmployeeProfile.objects.create(
            user=user,
            department=random.choice(departments),
            is_department_head=random.choice([True, False])
        )

def main():
    # Clear existing data
    User.objects.all().delete()
    Department.objects.all().delete()
    Project.objects.all().delete()
    Event.objects.all().delete()
    News.objects.all().delete()
    EmployeeProfile.objects.all().delete()

    # Create new data
    users = create_users(20)
    departments = create_departments()
    create_projects(users)
    create_events()
    create_news()
    create_employee_profiles(users, departments)

    print("Sample data has been created successfully!")

if __name__ == "__main__":
    main()