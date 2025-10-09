"""Parser for Strong app workout exports."""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dateutil import parser as date_parser
import dateparser

logger = logging.getLogger(__name__)


class WorkoutSet:
    """Represents a single set in an exercise."""

    def __init__(self, set_number: int, weight: Optional[float], reps: Optional[int],
                 duration: Optional[str], is_warmup: bool = False):
        self.set_number = set_number
        self.weight = weight
        self.reps = reps
        self.duration = duration
        self.is_warmup = is_warmup

    def __repr__(self):
        if self.duration:
            return f"Set {self.set_number}: {self.duration}"
        parts = []
        if self.is_warmup:
            parts.append("Warmup")
        if self.weight:
            parts.append(f"{self.weight} kg")
        if self.reps:
            parts.append(f"{self.reps} reps")
        return f"Set {self.set_number}: {' × '.join(parts) if parts else 'Bodyweight'}"


class Exercise:
    """Represents an exercise with multiple sets."""

    def __init__(self, name: str):
        self.name = name
        self.sets: List[WorkoutSet] = []

    def add_set(self, workout_set: WorkoutSet):
        self.sets.append(workout_set)

    def get_total_volume(self) -> float:
        """Calculate total volume (weight × reps) for this exercise."""
        return sum((s.weight or 0) * (s.reps or 0) for s in self.sets)

    def __repr__(self):
        return f"{self.name} ({len(self.sets)} sets)"


class Workout:
    """Represents a complete workout."""

    def __init__(self, name: str, date: datetime):
        self.name = name
        self.date = date
        self.exercises: List[Exercise] = []

    def add_exercise(self, exercise: Exercise):
        self.exercises.append(exercise)

    def get_total_volume(self) -> float:
        """Calculate total workout volume."""
        return sum(ex.get_total_volume() for ex in self.exercises)

    def get_total_sets(self) -> int:
        """Calculate total number of sets."""
        return sum(len(ex.sets) for ex in self.exercises)

    def estimate_duration(self) -> int:
        """Estimate workout duration in seconds based on sets and exercises."""
        # Rough estimation: 2 minutes per set + 1 minute per exercise transition
        total_sets = self.get_total_sets()
        num_exercises = len(self.exercises)
        estimated_seconds = (total_sets * 120) + (num_exercises * 60)
        return estimated_seconds

    def __repr__(self):
        return f"{self.name} on {self.date.strftime('%Y-%m-%d')} ({len(self.exercises)} exercises)"


class StrongParser:
    """Parser for Strong app workout text exports."""

    # Regex patterns for parsing
    # Matches: "Série 1: +10 kg × 20 reps" or "Set 1: 20 kg × 12 reps" or "W: 40 kg × 10 reps"
    SET_PATTERN = re.compile(
        r'(?:Série|Set|W:)\s*(\d+)?:?\s*(?:\+)?(\d+(?:\.\d+)?)\s*kg\s*×\s*(\d+)\s*reps?',
        re.IGNORECASE
    )

    # Matches: "Série 1: 15 reps" (bodyweight)
    BODYWEIGHT_PATTERN = re.compile(
        r'(?:Série|Set)\s*(\d+):?\s*(\d+)\s*reps?',
        re.IGNORECASE
    )

    # Matches: "Série 1: 7:00" (duration)
    DURATION_PATTERN = re.compile(
        r'(?:Série|Set)\s*(\d+):?\s*([\d:]+)',
        re.IGNORECASE
    )

    # Matches dates in various formats
    DATE_PATTERN = re.compile(
        r'(?:segunda|terça|quarta|quinta|sexta|sábado|domingo|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        re.IGNORECASE
    )

    @staticmethod
    def is_strong_workout(text: str) -> bool:
        """Check if the text appears to be a Strong app workout export."""
        # Look for characteristic patterns
        has_set_marker = bool(re.search(r'(?:Série|Set)\s*\d+:', text, re.IGNORECASE))
        has_weight_reps = bool(re.search(r'\d+\s*kg\s*×\s*\d+\s*reps?', text, re.IGNORECASE))
        has_link = 'strong.app' in text.lower()

        return has_set_marker or has_weight_reps or has_link

    @staticmethod
    def parse_workout(text: str) -> Optional[Workout]:
        """Parse a Strong app workout text export into a Workout object."""
        try:
            lines = text.strip().split('\n')

            # Extract workout name (first line)
            workout_name = lines[0].strip() if lines else "Workout"

            # Extract date (second line typically contains the date)
            workout_date = datetime.now()
            if len(lines) > 1:
                try:
                    # Try to parse the date from the second line
                    date_line = lines[1].strip()
                    logger.debug(f"Original date line: '{date_line}'")

                    # Remove day of week names that might interfere with parsing
                    date_line_clean = re.sub(
                        r'(segunda|terça|quarta|quinta|sexta|sábado|domingo|monday|tuesday|wednesday|thursday|friday|saturday|sunday)-feira,?\s*',
                        '', date_line, flags=re.IGNORECASE
                    )
                    logger.debug(f"Cleaned date line: '{date_line_clean}'")

                    # Use dateparser which supports Portuguese and English month names
                    parsed_date = dateparser.parse(
                        date_line_clean,
                        languages=['pt', 'en'],
                        settings={
                            'PREFER_DATES_FROM': 'past',
                            'RELATIVE_BASE': datetime.now()
                        }
                    )

                    if parsed_date:
                        workout_date = parsed_date
                        logger.info(f"Successfully parsed date: {workout_date.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        # Fallback to dateutil if dateparser fails
                        logger.warning("dateparser returned None, trying dateutil fallback")
                        workout_date = date_parser.parse(date_line_clean, fuzzy=True)
                        logger.info(f"Fallback parsed date: {workout_date.strftime('%Y-%m-%d %H:%M')}")

                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse date from '{lines[1]}': {e}")
                    logger.warning("Using current date/time as fallback")

            workout = Workout(workout_name, workout_date)
            current_exercise = None

            for line in lines[2:]:  # Skip name and date lines
                line = line.strip()
                if not line or line.startswith('http'):
                    continue

                # Check if this is a set line
                set_match = StrongParser.SET_PATTERN.search(line)
                bodyweight_match = StrongParser.BODYWEIGHT_PATTERN.search(line)
                duration_match = StrongParser.DURATION_PATTERN.search(line)

                if set_match or bodyweight_match or duration_match:
                    if current_exercise is None:
                        # Set without an exercise name - skip
                        continue

                    # Parse set information
                    if set_match:
                        set_num_str, weight_str, reps_str = set_match.groups()
                        set_num = int(set_num_str) if set_num_str else len(current_exercise.sets) + 1
                        is_warmup = line.strip().startswith('W:')
                        workout_set = WorkoutSet(
                            set_number=set_num,
                            weight=float(weight_str),
                            reps=int(reps_str),
                            duration=None,
                            is_warmup=is_warmup
                        )
                        current_exercise.add_set(workout_set)
                    elif bodyweight_match:
                        set_num_str, reps_str = bodyweight_match.groups()
                        set_num = int(set_num_str) if set_num_str else len(current_exercise.sets) + 1
                        workout_set = WorkoutSet(
                            set_number=set_num,
                            weight=None,
                            reps=int(reps_str),
                            duration=None
                        )
                        current_exercise.add_set(workout_set)
                    elif duration_match:
                        set_num_str, duration_str = duration_match.groups()
                        set_num = int(set_num_str) if set_num_str else len(current_exercise.sets) + 1
                        workout_set = WorkoutSet(
                            set_number=set_num,
                            weight=None,
                            reps=None,
                            duration=duration_str
                        )
                        current_exercise.add_set(workout_set)
                else:
                    # This is likely an exercise name
                    if current_exercise:
                        workout.add_exercise(current_exercise)
                    current_exercise = Exercise(line)

            # Add the last exercise
            if current_exercise and current_exercise.sets:
                workout.add_exercise(current_exercise)

            if not workout.exercises:
                logger.warning("No exercises found in workout text")
                return None

            logger.info(f"Parsed workout: {workout}")
            return workout

        except Exception as e:
            logger.error(f"Error parsing workout: {e}", exc_info=True)
            return None

    @staticmethod
    def format_workout_description(workout: Workout) -> str:
        """Format workout as a readable description for intervals.icu."""
        lines = []

        for exercise in workout.exercises:
            lines.append(f"\n**{exercise.name}**")
            for workout_set in exercise.sets:
                if workout_set.duration:
                    lines.append(f"  Set {workout_set.set_number}: {workout_set.duration}")
                else:
                    parts = []
                    if workout_set.is_warmup:
                        parts.append("Warmup:")
                    if workout_set.weight:
                        parts.append(f"{workout_set.weight} kg")
                    if workout_set.reps:
                        parts.append(f"{workout_set.reps} reps")

                    set_desc = " × ".join(parts) if parts else "Bodyweight"
                    lines.append(f"  Set {workout_set.set_number}: {set_desc}")

        # Add summary statistics
        lines.append(f"\n**Summary**")
        lines.append(f"Total exercises: {len(workout.exercises)}")
        lines.append(f"Total sets: {workout.get_total_sets()}")
        total_volume = workout.get_total_volume()
        if total_volume > 0:
            lines.append(f"Total volume: {total_volume:,.0f} kg")

        return '\n'.join(lines)
