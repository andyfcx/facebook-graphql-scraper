# -*- coding: utf-8 -*-
import json
import os
import time
import base64
import platform
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class SessionManager:
    """
    Manages Facebook session persistence with encryption.

    Stores cookies and encrypted credentials in user's home directory.
    Provides session validation and automatic re-login capabilities.

    Storage location: ~/.fb_scraper/ (default)
    Files:
        - session.json: Cookies and metadata
        - .credentials: Encrypted credentials
        - .key: Encryption key (machine-specific)
    """

    SESSION_FILE = 'session.json'
    CREDENTIALS_FILE = '.credentials'
    KEY_FILE = '.key'
    SESSION_TTL_DAYS = 7

    def __init__(self, storage_dir: str = '~/.fb_scraper'):
        """
        Initialize SessionManager.

        Args:
            storage_dir: Directory to store session files (default: ~/.fb_scraper)
        """
        self.storage_dir = Path(storage_dir).expanduser()
        self._ensure_storage_dir()
        self._cipher = self._get_cipher()

    def _ensure_storage_dir(self):
        """Create storage directory with secure permissions."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            # Set directory permissions to 700 (owner only)
            os.chmod(self.storage_dir, 0o700)
        except OSError as e:
            print(f"Warning: Could not create or set permissions on {self.storage_dir}: {e}")

    def _get_machine_id(self) -> bytes:
        """
        Generate machine-specific identifier.

        Combines hostname and MAC address for machine-specific key derivation.
        This ensures credentials are only decryptable on the same machine.

        Returns:
            Machine identifier as bytes
        """
        # Combine platform info for machine-specific key
        machine_data = f"{platform.node()}-{uuid.getnode()}"
        return machine_data.encode()

    def _get_cipher(self) -> Fernet:
        """
        Get or create encryption cipher.

        Uses PBKDF2 to derive encryption key from machine-specific identifier.
        Key is stored in .key file for consistency across sessions.

        Returns:
            Fernet cipher instance
        """
        key_path = self.storage_dir / self.KEY_FILE

        try:
            if key_path.exists():
                with open(key_path, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key from machine ID
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'fb_scraper_salt',  # Static salt for consistency
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(
                    kdf.derive(self._get_machine_id())
                )
                with open(key_path, 'wb') as f:
                    f.write(key)
                os.chmod(key_path, 0o600)

            return Fernet(key)
        except Exception as e:
            print(f"Warning: Error initializing cipher: {e}")
            # Return a basic cipher as fallback (less secure but allows operation)
            fallback_key = Fernet.generate_key()
            return Fernet(fallback_key)

    def _encrypt_credentials(self, credentials: Dict[str, str]) -> bytes:
        """
        Encrypt credentials dictionary.

        Args:
            credentials: Dictionary with 'fb_account' and 'fb_pwd' keys

        Returns:
            Encrypted credentials as bytes
        """
        json_str = json.dumps(credentials)
        return self._cipher.encrypt(json_str.encode())

    def _decrypt_credentials(self, encrypted_data: bytes) -> Dict[str, str]:
        """
        Decrypt credentials dictionary.

        Args:
            encrypted_data: Encrypted credentials bytes

        Returns:
            Dictionary with 'fb_account' and 'fb_pwd' keys
        """
        json_str = self._cipher.decrypt(encrypted_data).decode()
        return json.loads(json_str)

    def save_session(self, cookies: List[Dict], credentials: Optional[Dict[str, str]] = None,
                    metadata: Optional[Dict] = None):
        """
        Save session to disk.

        Args:
            cookies: List of cookie dictionaries from Selenium driver
            credentials: Optional dict with 'fb_account' and 'fb_pwd' keys
            metadata: Optional metadata dict (user_agent, login_url, etc.)
        """
        try:
            # Save cookies
            session_data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'cookies': cookies,
                'metadata': metadata or {}
            }

            session_path = self.storage_dir / self.SESSION_FILE
            with open(session_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            os.chmod(session_path, 0o600)

            print(f"Session saved to {session_path}")

            # Save credentials if provided
            if credentials:
                encrypted = self._encrypt_credentials(credentials)
                creds_path = self.storage_dir / self.CREDENTIALS_FILE
                with open(creds_path, 'wb') as f:
                    f.write(encrypted)
                os.chmod(creds_path, 0o600)
                print(f"Credentials saved to {creds_path}")

        except Exception as e:
            print(f"Error saving session: {e}")

    def load_session(self) -> Optional[Dict]:
        """
        Load session from disk.

        Returns:
            Dictionary with 'cookies', 'credentials', 'metadata' keys, or None if no session exists
        """
        try:
            session_path = self.storage_dir / self.SESSION_FILE
            if not session_path.exists():
                return None

            # Load cookies
            with open(session_path, 'r') as f:
                session_data = json.load(f)

            result = {
                'cookies': session_data.get('cookies', []),
                'metadata': session_data.get('metadata', {}),
                'credentials': None
            }

            # Load credentials if they exist
            creds_path = self.storage_dir / self.CREDENTIALS_FILE
            if creds_path.exists():
                try:
                    with open(creds_path, 'rb') as f:
                        encrypted = f.read()
                    result['credentials'] = self._decrypt_credentials(encrypted)
                except Exception as e:
                    print(f"Warning: Could not decrypt credentials: {e}")
                    # Delete corrupted credentials file
                    try:
                        creds_path.unlink()
                    except:
                        pass

            return result

        except json.JSONDecodeError as e:
            print(f"Error: Corrupted session file: {e}")
            # Clear corrupted session
            self.clear_session()
            return None
        except Exception as e:
            print(f"Error loading session: {e}")
            return None

    def has_valid_session(self) -> bool:
        """
        Quick check if a valid session exists.

        Checks if session file exists and is not too old (TTL check).
        Does not validate actual cookie validity with Facebook.

        Returns:
            True if session file exists and is recent, False otherwise
        """
        try:
            session_path = self.storage_dir / self.SESSION_FILE
            if not session_path.exists():
                return False

            # Check file modification time
            mtime = session_path.stat().st_mtime
            age_days = (time.time() - mtime) / (60 * 60 * 24)

            if age_days > self.SESSION_TTL_DAYS:
                print(f"Session file is {age_days:.1f} days old (TTL: {self.SESSION_TTL_DAYS} days)")
                return False

            return True

        except Exception as e:
            print(f"Error checking session validity: {e}")
            return False

    def clear_session(self):
        """Delete all session files."""
        try:
            session_path = self.storage_dir / self.SESSION_FILE
            creds_path = self.storage_dir / self.CREDENTIALS_FILE

            if session_path.exists():
                session_path.unlink()
                print(f"Deleted session file: {session_path}")

            if creds_path.exists():
                creds_path.unlink()
                print(f"Deleted credentials file: {creds_path}")

        except Exception as e:
            print(f"Error clearing session: {e}")

    def validate_session_with_driver(self, driver) -> bool:
        """
        Validate session by checking if cookies work with Facebook.

        This method loads cookies into the driver and checks if we're logged in.
        Should be called after inject_cookies_into_driver.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            True if session is valid (logged in), False otherwise
        """
        try:
            # Navigate to Facebook home
            current_url = driver.current_url
            if 'facebook.com' not in current_url:
                driver.get('https://www.facebook.com')
                time.sleep(3)

            # Check if on login page
            if 'login' in driver.current_url.lower():
                print("Session validation failed: Redirected to login page")
                return False

            # Check for login form (indicates NOT logged in)
            try:
                login_forms = driver.find_elements('css selector', '[data-testid="royal_login_form"]')
                if login_forms:
                    print("Session validation failed: Login form detected")
                    return False
            except:
                pass

            # Check for profile elements (indicates logged in)
            try:
                # Look for navigation elements that only appear when logged in
                profile_elements = driver.find_elements('css selector', '[aria-label*="Account"]')
                if not profile_elements:
                    profile_elements = driver.find_elements('css selector', '[aria-label*="Your profile"]')
                if not profile_elements:
                    # Check for presence of feed or other logged-in indicators
                    profile_elements = driver.find_elements('css selector', '[role="feed"]')

                if profile_elements:
                    print("Session validation successful: User is logged in")
                    return True
            except Exception as e:
                print(f"Error checking for profile elements: {e}")

            # If we can't definitively determine, assume not logged in
            print("Session validation failed: Could not confirm login status")
            return False

        except Exception as e:
            print(f"Error validating session: {e}")
            return False
