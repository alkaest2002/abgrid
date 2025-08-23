"""JWT token generator with expiration and UUID support.

Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201
# ruff: noqa: UP017

import argparse
import os
import sys
import urllib.parse
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
import yaml
from dotenv import load_dotenv


# Exit codes
EXIT_SUCCESS: int = 0
EXIT_APP_ERROR: int = 1
EXIT_SYSTEM_ERROR: int = 2
EXIT_USER_INTERRUPT: int = 130

# Load environment variables once at module level
load_dotenv()

@dataclass
class Config:
    """Configuration settings container for the license application.

    Contains default values for JWT algorithm, output directory paths,
    security requirements, and supported date formats for parsing.
    """

    algorithm: str = "HS256"
    output_dir: Path = Path("./licenser/licenses")
    min_secret_length: int = 32
    date_formats: list[str] = field(default_factory=lambda: [
        "%Y-%m-%d", "%Y-%m-%d %H:%M",
        "%Y/%m/%d", "%Y/%m/%d %H:%M",
    ])

class LicenseError(Exception):
    """Base exception for all license-related errors."""

class SecretKeyError(LicenseError):
    """Raised when secret key is missing, invalid, or not configured properly."""

class TokenGenerationError(LicenseError):
    """Raised when JWT token generation fails due to encoding or validation errors."""

class TokenVerificationError(LicenseError):
    """Raised when JWT token verification fails due to expiration, invalid signature, or malformed token."""

class DateParsingError(LicenseError):
    """Raised when date string cannot be parsed using any of the supported date formats."""

class JWTGenerator:
    """Handles JWT token generation, verification, and secret key management.

    Manages JWT operations including token creation with UUID subjects,
    token verification with issuer validation, and secret key strength validation.
    Requires AUTH_SECRET environment variable to be set.
    """

    def __init__(self, config: Config) -> None:
        """Initialize JWT generator with configuration and secret key validation.

        Args:
            config: Application configuration containing algorithm and security settings.

        Raises:
            SecretKeyError: If AUTH_SECRET environment variable is not set.
        """
        self.config = config

        # Handle secret key priority: env var > raise error
        env_secret = os.getenv("AUTH_SECRET")
        if not env_secret:
            error_message = "No secret key provided in AUTH_SECRET environment variable"
            raise SecretKeyError(error_message)

        self.secret_key = env_secret
        self.algorithm = config.algorithm

        # Validate secret key strength
        self.validate_secret_strength()

    def validate_secret_strength(self) -> None:
        """Validate secret key meets minimum security requirements.

        Prints a warning if the secret key is shorter than the configured minimum length.
        Does not raise an exception to allow operation with weak keys if necessary.
        """
        if len(self.secret_key) < self.config.min_secret_length:
            print(f"Security Warning: Secret key should be at least {self.config.min_secret_length} characters.")
            print(f"Current length: {len(self.secret_key)} characters")

    def get_secret_info(self) -> dict[str, Any]:
        """Get information about the current secret key configuration.

        Returns:
            Dictionary containing secret key length, algorithm, and strength assessment.
        """
        return {
            "length": len(self.secret_key),
            "algorithm": self.algorithm,
            "is_strong": len(self.secret_key) >= self.config.min_secret_length,
        }

    def generate_token(self, expiration_date: datetime) -> tuple[str, str]:
        """Generate a JWT token with UUID subject and expiration validation.

        Args:
            expiration_date: Token expiration datetime (will be converted to UTC if timezone-naive).

        Returns:
            Tuple of (jwt_token_string, generated_uuid).

        Raises:
            TokenGenerationError: If expiration date is in the past or token encoding fails.
        """
        user_uuid = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Ensure timezone awareness
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)

        # Validate expiration is in the future
        if expiration_date <= now:
            error_message = "Expiration date must be in the future"
            raise TokenGenerationError(error_message)

        payload = {
            "sub": user_uuid,
            "iat": now,
            "exp": expiration_date,
            "iss": "ab-grid",
        }

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        except Exception as e:
            error_message = f"Failed to generate token: {e}"
            raise TokenGenerationError(error_message) from e

        return token, user_uuid

    def verify_token(self, token: str) -> Any:
        """Verify and decode a JWT token with issuer validation.

        Args:
            token: The JWT token string to verify.

        Returns:
            Decoded token payload dictionary containing claims.

        Raises:
            TokenVerificationError: If token is expired, has invalid issuer, invalid signature, or malformed.
        """
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer="ab-grid"
            )
        except jwt.ExpiredSignatureError:
            error_message = "Token has expired"
            raise TokenVerificationError(error_message) from None
        except jwt.InvalidIssuerError:
            error_message = "Token issuer is invalid"
            raise TokenVerificationError(error_message) from None
        except Exception as e:
            error_message = f"Token verification failed: {e}"
            raise TokenVerificationError(error_message) from e

class Command(ABC):
    """Abstract base class for all license management commands.

    Provides common functionality for command execution including date parsing
    and email filename conversion utilities.
    """

    def __init__(self, args: argparse.Namespace, config: Config) -> None:
        """Initialize command with parsed CLI arguments and application configuration.

        Args:
            args: Parsed command line arguments.
            config: Application configuration settings.
        """
        self.args = args
        self.config = config

    @abstractmethod
    def execute(self) -> None:
        """Execute the specific command logic. Must be implemented by subclasses."""

    def parse_expiration_date(self, date_string: str) -> datetime:
        """Parse date string using configured formats, returning UTC datetime.

        Args:
            date_string: Date string to parse.

        Returns:
            Parsed datetime with UTC timezone.

        Raises:
            DateParsingError: If date string doesn't match any supported format.
        """
        for fmt in self.config.date_formats:
            try:
                return datetime.strptime(date_string, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        error_message = f"Could not parse date '{date_string}'. Supported formats: {', '.join(self.config.date_formats[:3])}, etc."
        raise DateParsingError(error_message)

    def email_to_safe_filename(self, email: str) -> str:
        """Convert email address to URL-encoded safe filename.

        Args:
            email: Email address to convert.

        Returns:
            URL-encoded string safe for use as filename.
        """
        return urllib.parse.quote(email, safe="")

    def safe_filename_to_email(self, filename: str) -> str:
        """Convert URL-encoded filename back to original email address.

        Args:
            filename: URL-encoded filename (with or without .yaml extension).

        Returns:
            Original email address.
        """
        base_name = filename.replace(".yaml", "")
        return urllib.parse.unquote(base_name)

class GenerateCommand(Command):
    """Command for generating new JWT tokens and saving metadata to YAML files.

    Creates JWT tokens with UUID subjects, validates expiration dates,
    and saves comprehensive metadata including token data to YAML files
    organized by email address.
    """

    def execute(self) -> None:
        """Execute JWT token generation with validation and file output.

        Validates required arguments, parses expiration date, generates token,
        saves metadata to YAML file, and displays generation summary.

        Raises:
            LicenseError: If required arguments are missing or expiration date is invalid.
        """
        # Validate required arguments
        if not self.args.email:
            error_message = "Email address required for token generation"
            raise LicenseError(error_message)

        if not self.args.expiration:
            error_message = "Expiration date required for token generation"
            raise LicenseError(error_message)

        # Parse and validate expiration date
        expiration_date = self.parse_expiration_date(self.args.expiration)
        if expiration_date <= datetime.now(timezone.utc):
            error_message = "Expiration date is in the past"
            raise LicenseError(error_message)

        # Generate token
        generator = JWTGenerator(self.config)
        token, final_uuid = generator.generate_token(expiration_date)

        # Create filename and save
        safe_email = self.email_to_safe_filename(self.args.email)
        output_filename = f"{safe_email}.yaml"
        output_path = self.config.output_dir / output_filename

        self.save_token_data(expiration_date, final_uuid, self.args.email,
                             output_path, token, generator)

        # Display summary
        print(f"Generated UUID: {final_uuid}")
        print("\nJWT TOKEN GENERATION SUMMARY")
        print("=" * 50)
        print(f"Email: {self.args.email}")
        print(f"UUID: {final_uuid}")
        print(f"Expiration: {expiration_date}")
        print(f"Algorithm: {generator.algorithm}")
        print(f"Token: {token}")
        print("=" * 50)

    def save_token_data(self, expiration_date: datetime, user_uuid: str,
                        email: str, output_path: Path, token: str,
                        generator: JWTGenerator) -> None:
        """Save JWT token metadata to YAML file with comprehensive information.

        Creates output directory if needed and saves token data including
        UUID, email, expiration details, generation timestamp, algorithm info,
        secret strength assessment, and the actual token.

        Args:
            expiration_date: Token expiration datetime.
            user_uuid: Generated UUID for the token subject.
            email: Email address associated with the token.
            output_path: Path where YAML file should be saved.
            token: Generated JWT token string.
            generator: JWT generator instance for accessing configuration.
        """
        secret_info = generator.get_secret_info()

        data = {
            "uuid": user_uuid,
            "email": email,
            "expiration_date": expiration_date.isoformat(),
            "expiration_timestamp": int(expiration_date.timestamp()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "algorithm": generator.algorithm,
            "secret_strength": "strong" if secret_info["is_strong"] else "weak",
            "token": token
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml.dump(data, default_flow_style=False, indent=2))
        print(f"Token data saved to: {output_path}")

class VerifyCommand(Command):
    """Command for verifying JWT token validity and displaying token information.

    Verifies JWT tokens against the configured secret and issuer,
    displays verification results, and attempts to show token information
    even for invalid tokens when possible.
    """

    def execute(self) -> None:
        """Execute JWT token verification and display results.

        Verifies the token and displays validation status, subject UUID, and expiration.
        For invalid tokens, attempts to display unverified payload information.
        """
        generator = JWTGenerator(self.config)

        print("\nTOKEN VERIFICATION")
        print("=" * 50)

        try:
            decoded = generator.verify_token(self.args.verify)
            print("Token is VALID")
            print(f"Subject UUID: {decoded.get('sub')}")
            exp_timestamp = decoded.get("exp", 0)
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            print(f"Expires At: {exp_datetime.isoformat()}")

        except TokenVerificationError as e:
            print(f"Token is INVALID: {e}")

            # Try to show basic info even for invalid tokens
            try:
                unverified_payload = jwt.decode(
                    self.args.verify,
                    options={"verify_signature": False, "verify_exp": False}
                )
                print("\nToken Information (Unverified):")
                print(f"Email: {unverified_payload.get('email', 'Not set')}")
                print(f"Subject: {unverified_payload.get('sub')}")
                exp_timestamp = unverified_payload.get("exp", 0)
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                print(f"Expires At: {exp_datetime.isoformat()}")
            except Exception:
                print("Could not decode token structure")

class SearchCommand(Command):
    """Command for searching and displaying stored token data by email address.

    Searches for YAML files containing token metadata based on email address,
    displays comprehensive token information including expiration status,
    and handles file parsing errors gracefully.
    """

    def execute(self) -> None:
        """Execute token data search by email address and display results.

        Looks for YAML files matching the email address, parses the stored data,
        and displays formatted token information including expiration status.

        Raises:
            LicenseError: If YAML parsing fails or file cannot be read.
        """
        email = self.args.search
        safe_email = self.email_to_safe_filename(email)
        expected_filename = f"{safe_email}.yaml"
        file_path = self.config.output_dir / expected_filename

        if not file_path.exists():
            print("❌ NO FILE FOUND for this email")
            return

        try:
            with file_path.open("r") as f:
                data = yaml.safe_load(f)

            print("FOUND TOKEN DATA")
            print("-" * 30)

            # Display the data in a formatted way
            print(f"Email: {data.get('email', 'Not found')}")
            print(f"UUID: {data.get('uuid', 'Not found')}")

            # Handle expiration date
            exp_date = data.get("expiration_date", "Not found")
            if exp_date != "Not found":
                try:
                    exp_datetime = datetime.fromisoformat(exp_date.replace("Z", "+00:00"))
                    is_expired = exp_datetime <= datetime.now(timezone.utc)
                    status = "EXPIRED" if is_expired else "VALID"
                    print(f"Expiration: {exp_date} ({status})")
                except Exception:
                    print(f"Expiration: {exp_date} (Could not parse)")
            else:
                print(f"Expiration: {exp_date}")

            # Handle generation date
            gen_date = data.get("generated_at", "Not found")
            print(f"Generated: {gen_date}")

            # Additional info
            print(f"Algorithm: {data.get('algorithm', 'Not found')} | "
                f"Strength: {data.get('secret_strength')}")
            print(f"Token: {data.get('token', 'Not found')}")

        except yaml.YAMLError as e:
            error_message = f"Failed to parse YAML file: {e}"
            raise LicenseError(error_message) from e
        except Exception as e:
            error_message = f"Could not read file: {e}"
            raise LicenseError(error_message) from e

class LicenseApp:
    """Main application class for JWT license management with command-line interface.

    Provides a terminal interface for JWT token operations including generation,
    verification, and search functionality. Handles argument parsing, command routing,
    and comprehensive error handling with appropriate exit codes.
    """

    def __init__(self) -> None:
        """Initialize the license application with configuration and available commands."""
        self.config = Config()
        self.commands: dict[str, type[Command]] = {
            "generate": GenerateCommand,
            "verify": VerifyCommand,
            "search": SearchCommand
        }

    def run(self) -> int:
        """Main application entry point with comprehensive error handling and exit codes.

        Parses command line arguments, validates them, determines the appropriate action,
        and executes the corresponding command with proper error handling.

        Returns:
            Exit code: 0 for success, 1 for application errors, 2 for system errors, 130 for user interrupt.
        """
        try:
            # Parse and validate arguments
            args = self.parse_args()
            self.validate_args(args)

            # Determine action based on arguments
            action = self.determine_action(args)

            command = self.commands[action](args, self.config)
            command.execute()

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return EXIT_USER_INTERRUPT
        except LicenseError as error:
            print(f"❌ Error: {error}")
            return EXIT_APP_ERROR
        except Exception as error:
            print(f"❌ Unexpected error: {error}")
            return EXIT_SYSTEM_ERROR
        else:
            return EXIT_SUCCESS

    def determine_action(self, args: argparse.Namespace) -> str:
        """Determine which command action to execute based on parsed arguments.

        Args:
            args: Parsed command line arguments.

        Returns:
            Command action string: "verify", "search", or "generate" (default).
        """
        if args.verify:
            return "verify"
        if args.search:
            return "search"
        return "generate"

    def parse_args(self) -> argparse.Namespace:
        """Parse and structure command line arguments with mutually exclusive operations.

        Sets up argument parser with generate (default), verify, and search operations
        as mutually exclusive options, along with email and expiration arguments
        for token generation.

        Returns:
            Parsed command line arguments namespace.
        """
        parser = argparse.ArgumentParser(
            description="Generate JWT token with expiration and UUID. Requires AUTH_SECRET to be configured.",
            epilog="Examples:\n"
                   "  python create_license.py --generate -e user@example.com -x '2024-12-31'\n"
                   "  python create_license.py --email user@example.com --expiration '2024-12-31'\n"
                   "  python create_license.py --verify 'your.jwt.token.here'\n"
                   "  python create_license.py --search user@example.com",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # Mutually exclusive group for main operations
        group = parser.add_mutually_exclusive_group()

        # Token generation arguments (default)
        group.add_argument("--generate", action="store_true",
                          help="Generate a new JWT token (default action)")

        # Token verification argument
        group.add_argument("--verify",
                          help="Verify an existing JWT token")

        # Token search argument
        group.add_argument("--search",
                          help="Search for token data by email address")

        # Arguments for token generation
        parser.add_argument("-e", "--email",
                           help="Email address (required for token generation)")
        parser.add_argument("-x", "--expiration",
                           help="Expiration date (required for token generation)")

        return parser.parse_args()

    def validate_args(self, args: argparse.Namespace) -> None:
        """Validate parsed command line arguments for required fields.

        Ensures that token generation operations have required email and expiration arguments.

        Args:
            args: Parsed command line arguments.

        Raises:
            LicenseError: If required arguments are missing for token generation.
        """
        # For generation (default action or explicit --generate)
        if not args.verify and not args.search:
            if not args.email:
                error_message = "Email address required for token generation"
                raise LicenseError(error_message)
            if not args.expiration:
                error_message = "Expiration date required for token generation"
                raise LicenseError(error_message)

def main() -> int:
    """Entry point for the JWT license management application.

    Creates and runs the main LicenseApp instance.

    Returns:
        Application exit code.
    """
    app = LicenseApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())
