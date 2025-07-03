"""
Data storage module for managing tournament registrations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DataStorage:
    """Manages tournament registration data in memory with persistence"""
    
    def __init__(self):
        # Main player data structure
        self.players: Dict[str, Dict[str, Dict[str, Any]]] = {
            "vsa": {},  # VSA tournament players
            "h2h": {}   # H2H tournament players
        }
        
        # Temporary registrations awaiting confirmation
        self.temp_registrations: Dict[str, Dict[str, Any]] = {}
        
        # Statistics tracking
        self.stats = {
            "total_registrations": 0,
            "confirmed_registrations": 0,
            "last_registration_time": None
        }
        
        # Load persisted data if exists
        self._load_data()
    
    def _load_data(self) -> None:
        """Load data from persistent storage"""
        try:
            with open("tournament_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.players = data.get("players", {"vsa": {}, "h2h": {}})
                self.temp_registrations = data.get("temp_registrations", {})
                self.stats = data.get("stats", {
                    "total_registrations": 0,
                    "confirmed_registrations": 0,
                    "last_registration_time": None
                })
            logger.info("Loaded tournament data from file")
        except FileNotFoundError:
            logger.info("No existing tournament data found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading tournament data: {e}")
    
    def _save_data(self) -> None:
        """Save data to persistent storage"""
        try:
            data = {
                "players": self.players,
                "temp_registrations": self.temp_registrations,
                "stats": self.stats,
                "last_updated": datetime.now().isoformat()
            }
            with open("tournament_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("Saved tournament data to file")
        except Exception as e:
            logger.error(f"Error saving tournament data: {e}")
    
    async def save_temp_registration(
        self,
        user_id: int,
        username: str,
        tournament_type: str,
        team_name: str,
        rating: int
    ) -> bool:
        """
        Save a temporary registration awaiting admin confirmation
        
        Args:
            user_id: Telegram user ID
            username: Telegram username
            tournament_type: 'vsa' or 'h2h'
            team_name: Team name
            rating: Player rating
            
        Returns:
            True if saved successfully
        """
        try:
            # Check for existing registration
            username_key = f"@{username}" if not username.startswith('@') else username
            
            if username_key in self.players.get(tournament_type, {}):
                logger.warning(f"User {username} already registered for {tournament_type}")
                return False
            
            # Save temporary registration
            self.temp_registrations[str(user_id)] = {
                "username": username,
                "tournament_type": tournament_type,
                "team_name": team_name,
                "rating": rating,
                "timestamp": datetime.now().isoformat(),
                "confirmed": False
            }
            
            # Update stats
            self.stats["total_registrations"] += 1
            self.stats["last_registration_time"] = datetime.now().isoformat()
            
            self._save_data()
            
            logger.info(f"Saved temp registration for {username} in {tournament_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving temp registration: {e}")
            return False
    
    def confirm_registration(self, user_id: str) -> bool:
        """
        Confirm a temporary registration and move it to main players
        
        Args:
            user_id: User ID as string
            
        Returns:
            True if confirmed successfully
        """
        try:
            temp_data = self.temp_registrations.get(str(user_id))
            if not temp_data:
                logger.warning(f"No temp registration found for user {user_id}")
                return False
            
            # Move to main players data
            tournament_type = temp_data["tournament_type"]
            username = temp_data["username"]
            username_key = f"@{username}" if not username.startswith('@') else username
            
            self.players[tournament_type][username_key] = {
                "name": temp_data["team_name"],
                "stars": temp_data["rating"],
                "confirmed": True,
                "confirmation_time": datetime.now().isoformat(),
                "registration_time": temp_data["timestamp"]
            }
            
            # Remove from temp registrations
            del self.temp_registrations[str(user_id)]
            
            # Update stats
            self.stats["confirmed_registrations"] += 1
            
            self._save_data()
            
            logger.info(f"Confirmed registration for {username} in {tournament_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error confirming registration: {e}")
            return False
    
    def get_all_players(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all confirmed players"""
        return self.players.copy()
    
    def get_temp_registrations(self) -> Dict[str, Dict[str, Any]]:
        """Get all temporary registrations"""
        return self.temp_registrations.copy()
    
    def get_player(self, username: str, tournament_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific player's data
        
        Args:
            username: Player username
            tournament_type: 'vsa' or 'h2h'
            
        Returns:
            Player data or None if not found
        """
        username_key = f"@{username}" if not username.startswith('@') else username
        return self.players.get(tournament_type, {}).get(username_key)
    
    def is_registered(self, username: str, tournament_type: str) -> bool:
        """
        Check if a user is already registered for a tournament
        
        Args:
            username: Player username
            tournament_type: 'vsa' or 'h2h'
            
        Returns:
            True if already registered
        """
        return self.get_player(username, tournament_type) is not None
    
    def has_temp_registration(self, user_id: int, tournament_type: str) -> bool:
        """
        Check if user has a pending registration
        
        Args:
            user_id: Telegram user ID
            tournament_type: 'vsa' or 'h2h'
            
        Returns:
            True if has pending registration
        """
        temp_data = self.temp_registrations.get(str(user_id))
        return temp_data is not None and temp_data.get("tournament_type") == tournament_type
    
    def clear_all_data(self) -> None:
        """Clear all tournament data"""
        self.players = {"vsa": {}, "h2h": {}}
        self.temp_registrations = {}
        self.stats = {
            "total_registrations": 0,
            "confirmed_registrations": 0,
            "last_registration_time": None
        }
        self._save_data()
        logger.info("Cleared all tournament data")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tournament statistics"""
        vsa_total = len(self.players["vsa"])
        h2h_total = len(self.players["h2h"])
        vsa_confirmed = sum(1 for p in self.players["vsa"].values() if p.get("confirmed"))
        h2h_confirmed = sum(1 for p in self.players["h2h"].values() if p.get("confirmed"))
        
        return {
            "vsa_total": vsa_total,
            "h2h_total": h2h_total,
            "vsa_confirmed": vsa_confirmed,
            "h2h_confirmed": h2h_confirmed,
            "pending_confirmations": len(self.temp_registrations),
            "total_users": len(set(
                list(self.players["vsa"].keys()) + 
                list(self.players["h2h"].keys()) +
                [data["username"] for data in self.temp_registrations.values()]
            )),
            "last_registration_time": self.stats.get("last_registration_time")
        }
    
    async def periodic_cleanup(self) -> None:
        """Periodically clean up expired temporary registrations"""
        while True:
            try:
                current_time = datetime.now()
                expired_users = []
                
                for user_id, data in self.temp_registrations.items():
                    registration_time = datetime.fromisoformat(data["timestamp"])
                    if current_time - registration_time > timedelta(hours=24):
                        expired_users.append(user_id)
                
                # Remove expired registrations
                for user_id in expired_users:
                    del self.temp_registrations[user_id]
                    logger.info(f"Removed expired temp registration for user {user_id}")
                
                if expired_users:
                    self._save_data()
                
                # Sleep for 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                await asyncio.sleep(3600)  # Continue trying
