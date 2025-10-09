"""Client for interacting with the Intervals.icu API."""

import logging
import requests
from datetime import datetime
from typing import Dict, Optional
from strong_parser import Workout

logger = logging.getLogger(__name__)


class IntervalsClient:
    """Client for the Intervals.icu API."""

    BASE_URL = "https://intervals.icu/api/v1"

    def __init__(self, api_key: str, athlete_id: str):
        """
        Initialize the Intervals.icu client.

        Args:
            api_key: Your Intervals.icu API key
            athlete_id: Your athlete ID (use 0 for your own account)
        """
        self.api_key = api_key
        self.athlete_id = athlete_id
        self.session = requests.Session()
        self.session.auth = ('API_KEY', api_key)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Strong-To-Intervals-Bot/1.0'
        })

    def create_workout_activity(self, workout: Workout, description: str) -> Optional[Dict]:
        """
        Create a manual workout activity in Intervals.icu.

        Args:
            workout: Parsed Workout object from Strong app
            description: Formatted workout description

        Returns:
            API response as dict if successful, None otherwise
        """
        # Estimate training load based on volume
        # This is a rough estimation: volume / 1000
        total_volume = workout.get_total_volume()
        estimated_load = max(int(total_volume / 1000), 10) if total_volume > 0 else 50

        # Estimate duration
        duration_seconds = workout.estimate_duration()

        # Prepare activity payload
        activity_data = {
            "start_date_local": workout.date.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "WeightTraining",
            "name": workout.name,
            "description": description,
            "moving_time": duration_seconds,
            "icu_training_load": estimated_load
        }

        try:
            url = f"{self.BASE_URL}/athlete/{self.athlete_id}/activities/manual"
            logger.info(f"Creating manual workout activity at {url}")
            logger.debug(f"Activity data: {activity_data}")

            response = self.session.post(url, json=activity_data)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Successfully created workout activity: {result.get('id')}")
            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error creating workout: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating workout: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating workout: {e}", exc_info=True)
            return None

    def get_activity_url(self, activity_id: int) -> str:
        """
        Generate the URL to view the activity on Intervals.icu.

        Args:
            activity_id: The activity ID returned by the API

        Returns:
            URL to the activity on Intervals.icu
        """
        return f"https://intervals.icu/activities/{activity_id}"

    def test_connection(self) -> bool:
        """
        Test the API connection and credentials.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/athlete/{self.athlete_id}"
            response = self.session.get(url)
            response.raise_for_status()
            logger.info("API connection test successful")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"API connection test failed: {e}")
            return False
