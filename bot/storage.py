"""
Data storage module for tournament registrations
Handles persistent storage and retrieval of player data
"""

import json
import logging
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataStorage:
    """Handles data persistence for tournament registrations"""

    def __init__(self, data_file: str = "tournament_data.json"):
        self.data_file = data_file
        self.data = self._load_data()

        # Initialize structure if needed
        if "players" not in self.data:
            self.data["players"] = {"vsa": {}, "h2h": {}}
        if "temp_registrations" not in self.data:
            self.data["temp_registrations"] = {}
        if "metadata" not in self.data:
            self.data["metadata"] = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }

    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.info(f"Data file {self.data_file} not found, creating new")
                return {}
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {}

    def _save_data(self) -> bool:
        """Save data to JSON file"""
        try:
            self.data["metadata"]["last_updated"] = datetime.now().isoformat()

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False

    async def save_temp_registration(
        self,
        user_id: int,
        username: str,
        tournament_type: str,
        team_name: str,
        rating: int
    ) -> bool:
        """Save temporary registration pending admin confirmation"""
        try:
            # Check if user already has a confirmed registration for this tournament
            confirmed_players = self.data["players"].get(tournament_type, {})
            if username.lower() in [k.lower() for k in confirmed_players.keys()]:
                logger.warning(f"User {username} already registered for {tournament_type}")
                return False

            # Check if user already has a pending registration
            temp_regs = self.data["temp_registrations"]
            for existing_user_id, existing_data in temp_regs.items():
                if (existing_data.get("username", "").lower() == username.lower() and 
                    existing_data.get("tournament_type") == tournament_type):
                    logger.warning(f"User {username} already has pending registration for {tournament_type}")
                    return False

            # Save temporary registration
            self.data["temp_registrations"][str(user_id)] = {
                "username": username,
                "tournament_type": tournament_type,
                "team_name": team_name,
                "rating": rating,
                "timestamp": datetime.now().isoformat(),
                "confirmed": False
            }

            self._save_data()
            logger.info(f"Saved temp registration for {username}: {tournament_type}")
            return True

        except Exception as e:
            logger.error(f"Error saving temp registration: {e}")
            return False

    def confirm_registration(self, user_id: int) -> bool:
        """Подтверждение регистрации"""
        try:
            temp_registrations = self.get_temp_registrations()

            if str(user_id) not in temp_registrations:
                return False

            user_data = temp_registrations[str(user_id)]
            tournament_type = user_data["tournament_type"]

            # Перемещаем в основные игроки
            players = self.get_all_players()
            if tournament_type not in players:
                players[tournament_type] = {}

            players[tournament_type][user_data["username"]] = {
                "name": user_data["team_name"],
                "stars": user_data["rating"],
                "confirmed": True,
                "user_id": user_id,
                "registered_at": datetime.now().isoformat()
            }

            self._save_data("players.json", players)

            # Удаляем из временных
            del temp_registrations[str(user_id)]
            self._save_data("temp_registrations.json", temp_registrations)

            return True

        except Exception as e:
            logger.error(f"Ошибка подтверждения регистрации: {e}")
            return False

    def reject_registration(self, user_id: int) -> bool:
        """Отклонение регистрации"""
        try:
            temp_registrations = self.get_temp_registrations()

            if str(user_id) not in temp_registrations:
                return False

            # Просто удаляем из временных регистраций
            del temp_registrations[str(user_id)]
            self._save_data("temp_registrations.json", temp_registrations)

            return True

        except Exception as e:
            logger.error(f"Ошибка отклонения регистрации: {e}")
            return False

    def get_all_players(self) -> Dict[str, Dict[str, Any]]:
        """Get all confirmed players"""
        return self.data.get("players", {"vsa": {}, "h2h": {}})

    def get_temp_registrations(self) -> Dict[str, Any]:
        """Get all temporary registrations"""
        return self.data.get("temp_registrations", {})

    def remove_confirmed_player(self, tournament_type: str, username: str) -> bool:
        """Удаление подтвержденного игрока"""
        try:
            players = self.data.get("players", {})
            tournament_players = players.get(tournament_type, {})
            
            if username in tournament_players:
                del tournament_players[username]
                self._save_data()
                logger.info(f"Удален игрок {username} из турнира {tournament_type}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка удаления игрока: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get tournament statistics"""
        players = self.data.get("players", {})
        temp_regs = self.data.get("temp_registrations", {})

        vsa_total = len(players.get("vsa", {}))
        h2h_total = len(players.get("h2h", {}))

        vsa_confirmed = sum(1 for p in players.get("vsa", {}).values() if p.get("confirmed"))
        h2h_confirmed = sum(1 for p in players.get("h2h", {}).values() if p.get("confirmed"))

        # Get last registration time
        last_time = None
        all_times = []

        for tournament_data in players.values():
            for player_data in tournament_data.values():
                if "registered_at" in player_data:
                    all_times.append(player_data["registered_at"])

        for temp_data in temp_regs.values():
            if "timestamp" in temp_data:
                all_times.append(temp_data["timestamp"])

        if all_times:
            last_time = max(all_times)

        return {
            "vsa_total": vsa_total,
            "vsa_confirmed": vsa_confirmed,
            "h2h_total": h2h_total,
            "h2h_confirmed": h2h_confirmed,
            "pending_confirmations": len(temp_regs),
            "total_users": vsa_total + h2h_total,
            "last_registration_time": last_time
        }

    def clear_all_data(self) -> bool:
        """Clear all tournament data"""
        try:
            self.data = {
                "players": {"vsa": {}, "h2h": {}},
                "temp_registrations": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "cleared_at": datetime.now().isoformat()
                }
            }
            self._save_data()
            logger.info("All tournament data cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False

    async def cleanup_expired_registrations(self) -> None:
        """Clean up expired temporary registrations"""
        try:
            current_time = datetime.now()
            temp_regs = self.data["temp_registrations"]
            expired_users = []

            for user_id, reg_data in temp_regs.items():
                reg_time = datetime.fromisoformat(reg_data["timestamp"])
                if current_time - reg_time > timedelta(hours=24):  # 24 hour expiry
                    expired_users.append(user_id)

            for user_id in expired_users:
                del temp_regs[user_id]
                logger.info(f"Cleaned up expired registration for user {user_id}")

            if expired_users:
                self._save_data()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def periodic_cleanup(self) -> None:
        """Run periodic cleanup of expired data"""
        while True:
            try:
                await self.cleanup_expired_registrations()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(3600)