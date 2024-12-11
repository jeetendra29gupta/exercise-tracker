import logging
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, flash, redirect, url_for, session

from log_config import setup_logging
from models import DailyExerciseTracker, User, Session
from utils import session_token_required

setup_logging()
logger = logging.getLogger(__name__)

tracker_router = Blueprint('tracker', __name__)


@tracker_router.route("/add_exercise_tracker", methods=['GET', 'POST'])
@session_token_required
def add_exercise_tracker():
    username = session['user_name']

    with Session() as session_db:
        user = session_db.query(User).filter_by(username=username).first()

        if request.method == "POST":
            steps_taken = int(request.form['steps_taken'])
            distance = float(request.form['distance'])
            calories_burned = float(request.form['calories_burned'])
            max_heart_rate = int(request.form['max_heart_rate'])
            min_heart_rate = int(request.form['min_heart_rate'])
            exercise_duration = int(request.form['exercise_duration'])

            if not steps_taken or not distance or not calories_burned or not max_heart_rate or not min_heart_rate or not exercise_duration:
                message = "All fields are required."
                flash(message, "Error")
                logger.error(message)
                return redirect(url_for("tracker.add_tracker"))

            user_id = user.id

            new_exercise = DailyExerciseTracker(
                date=datetime.now(),
                steps_taken=steps_taken,
                distance=distance,
                calories_burned=calories_burned,
                max_heart_rate=max_heart_rate,
                min_heart_rate=min_heart_rate,
                avg_heart_rate=(max_heart_rate + min_heart_rate) // 2,
                exercise_duration=exercise_duration,
                user_id=user_id
            )

            session_db.add(new_exercise)
            session_db.commit()
            session_db.close()

            message = "Tracker added successfully."
            flash(message, "Success")
            return redirect(url_for("user.dashboard"))

        return render_template("add_tracker.html", user=user.fullname)


@tracker_router.route("/report/<action>")
@session_token_required
def tracker_report(action):
    if action not in ['by_steps', 'by_distance', 'by_calories', 'by_heart_rate', 'by_duration']:
        flash("Invalid report action.", "Error")
        return redirect(url_for("user.dashboard"))

    username = session['user_name']
    today = datetime.now()
    seven_days_ago = today - timedelta(days=7)

    with Session() as session_db:
        user = session_db.query(User).filter_by(username=username).first()

        if action == 'by_steps':
            tracker_data = session_db.query(DailyExerciseTracker.date, DailyExerciseTracker.steps_taken)
        elif action == 'by_distance':
            tracker_data = session_db.query(DailyExerciseTracker.date, DailyExerciseTracker.distance)
        elif action == 'by_calories':
            tracker_data = session_db.query(DailyExerciseTracker.date, DailyExerciseTracker.calories_burned)
        elif action == 'by_heart_rate':
            tracker_data = session_db.query(DailyExerciseTracker.date, DailyExerciseTracker.min_heart_rate,
                                            DailyExerciseTracker.max_heart_rate, DailyExerciseTracker.avg_heart_rate)
        elif action == 'by_duration':
            tracker_data = session_db.query(DailyExerciseTracker.date, DailyExerciseTracker.exercise_duration)

        tracker_data = tracker_data.filter(
            DailyExerciseTracker.user_id == user.id,
            DailyExerciseTracker.date >= seven_days_ago,
            DailyExerciseTracker.date <= today,
        ).all()
    return render_template("tracker_report.html", action=action, tracker_data=tracker_data)


@tracker_router.route("/update_exercise_tracker/<int:exercise_tracker_id>", methods=['GET', 'POST'])
@session_token_required
def update_exercise_tracker(exercise_tracker_id):
    username = session['user_name']

    with Session() as session_db:
        user = session_db.query(User).filter_by(username=username).first()
        exercise_to_update = session_db.query(DailyExerciseTracker).get(exercise_tracker_id)

        if not exercise_to_update:
            message = f"Exercise with ID {exercise_tracker_id} not found."
            flash(message, "Error")
            logger.error(message)
            return redirect(url_for("user.dashboard"))

        if exercise_to_update.user_id != user.id:
            message = "You are not authorized to update this exercise."
            flash(message, "Error")
            logger.error(message)
            return redirect(url_for("user.dashboard"))

        if request.method == "POST":
            steps_taken = int(request.form['steps_taken'])
            distance = float(request.form['distance'])
            calories_burned = float(request.form['calories_burned'])
            max_heart_rate = int(request.form['max_heart_rate'])
            min_heart_rate = int(request.form['min_heart_rate'])
            exercise_duration = int(request.form['exercise_duration'])

            if not steps_taken or not distance or not calories_burned or not max_heart_rate or not min_heart_rate or not exercise_duration:
                message = "All fields are required."
                flash(message, "Error")
                logger.error(message)
                return redirect(url_for("tracker.add_tracker"))

            user_id = user.id

            exercise_to_update.steps_taken = steps_taken
            exercise_to_update.distance = distance
            exercise_to_update.calories_burned = calories_burned
            exercise_to_update.max_heart_rate = max_heart_rate
            exercise_to_update.min_heart_rate = min_heart_rate
            exercise_to_update.avg_heart_rate = (max_heart_rate + min_heart_rate) // 2
            exercise_to_update.exercise_duration = exercise_duration

            session_db.add(exercise_to_update)
            session_db.commit()

            message = "Exercise tracker updated successfully."
            flash(message, "Success")
            logger.info(message)

            return redirect(url_for("user.dashboard"))

        return render_template("update_exercise_tracker.html", exercise_to_update=exercise_to_update)


@tracker_router.route("/delete_exercise_tracker/<int:exercise_tracker_id>")
@session_token_required
def delete_exercise_tracker(exercise_tracker_id):
    username = session['user_name']

    with Session() as session_db:
        user = session_db.query(User).filter_by(username=username).first()
        exercise_to_delete = session_db.query(DailyExerciseTracker).get(exercise_tracker_id)

        if not exercise_to_delete:
            message = f"Exercise with ID {exercise_tracker_id} not found."
            flash(message, "Error")
            logger.error(message)
            return redirect(url_for("user.dashboard"))

        if exercise_to_delete.user_id != user.id:
            message = "You are not authorized to delete this exercise."
            flash(message, "Error")
            logger.error(message)
            return redirect(url_for("user.dashboard"))

        session_db.delete(exercise_to_delete)
        session_db.commit()
        session_db.close()

        message = "Exercise deleted successfully."
        flash(message, "Success")
        return redirect(url_for("user.dashboard"))
