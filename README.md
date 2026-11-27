# PrepPilot

A mock interview API built with Django REST Framework. You pick an interview type and difficulty, get random questions from a question bank, answer them, and get a score for each answer plus an overall score for the session.

I wanted to prepare for my upcoming interviews while also practice my DRF skills. 

Still in progress. Auth, the question bank and the session flow work. Scoring is a placeholder for now; the plan is to replace it with an LLM call, and to let the LLM generate new questions too.

## What it does

- Two roles, Admin and Interviewee. Admins manage topics and questions. Interviewees take interviews.
- Sign up with an email, log in with either email or username (JWT).
- Interview types: Technical, HR, Behavioral. Topics like Python or SQL are used for technical ones.
- A session picks random questions that match the type and difficulty you chose, and the finished session score is the average of its answer scores.
- Interviewees only see their own sessions. Admins can see all of them.

## Stack

Python, Django 5.2, Django REST Framework, SimpleJWT, MySQL, python-decouple.

## Running it locally

```bash
git clone <repo-url>
cd <repo-folder>
python -m venv env
env\Scripts\activate          # macOS/Linux: source env/bin/activate
pip install django djangorestframework djangorestframework-simplejwt python-decouple mysqlclient
```

Create a MySQL database, then add a `.env` file next to `manage.py`:

```
SECRET_KEY=...
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
```

Then:

```bash
python manage.py makemigrations authentication Interviews
python manage.py migrate
python manage.py createsuperuser   # superusers get the Admin role
python manage.py runserver
```

## Endpoints

Send `Authorization: Bearer <access_token>` on everything except register and login.

**Auth**
- `POST /register/` with `email`, `username`, `first_name`, `password`
- `POST /login/` with `email` or `username`, plus `password`. Returns the tokens and your role.
- `GET /me/` returns the logged-in user

**Question bank**
- `GET /topics/` any logged-in user; `POST /topics/` admin
- `PUT`/`DELETE /topics/<id>/` admin
- `GET`/`POST /questions/` admin (filter with `?topic=`, `?interview_type=`, `?difficulty=`)
- `GET`/`PUT`/`DELETE /questions/<id>/` admin

**Sessions**
- `POST /sessions/` interviewee. Body: `topic`, `interview_type`, `difficulty`, `num_questions`
- `GET /sessions/` your sessions (all of them for admins)
- `GET /sessions/<uuid>/` one session with its questions and answers
- `POST /sessions/<uuid>/answers/<answer_id>/` with `answer_text`

Example question:

```json
{
  "text": "What is a decorator in Python?",
  "topic": 1,
  "interview_type": "technical",
  "difficulty": "Easy"
}
```

Values are case-sensitive: `technical`, `HR`, `Behavioral` and `Easy`, `Medium`, `Hard`.

## Notes

- Clients can't choose their own role. Everyone who registers is an Interviewee.
- Session IDs are UUIDs.
- A question or topic that's been used in a past session can't be deleted, so history stays intact.
- I've been testing the endpoints with Postman so far.

## To do

- [ ] LLM scoring and feedback
- [ ] LLM-generated questions
- [ ] Change and reset password
- [ ] Pagination
- [ ] Frontend
