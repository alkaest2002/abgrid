"""JWT token generator with expiration and UUID support.

Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201
# ruff: noqa: UP017

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
import yaml
from dotenv import load_dotenv


# Load environment variables once at module level
load_dotenv()

# Configuration constants
DEFAULT_ALGORITHM = "HS256"
DEFAULT_OUTPUT_DIR = Path("./")
MIN_SECRET_LENGTH = 32
DATE_FORMATS = [
    "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M",
]

class JWTGenerator:
    """Handles JWT token generation and verification."""

    def __init__(self) -> None:
        """Initialize JWT generator.

        Raises:
            SystemExit: If no secret key is available or configured.
        """
        # Handle secret key priority: explicit param > env var > exit
        env_secret = os.getenv("AUTH_SECRET")

        if env_secret:
            # Environment variable available
            self.secret_key = env_secret
        else:
            # No secret configured - exit with error
            self._exit_no_secret()

        # Handle algorithm
        self.algorithm = os.getenv("JWT_ALGORITHM", DEFAULT_ALGORITHM)

        # Validate secret key strength
        self._validate_secret_strength()

    def _exit_no_secret(self) -> None:
        """Exit the application when no secret key is available."""
        print("❌ Error: No secret key provided!")
        sys.exit(1)

    def _validate_secret_strength(self) -> None:
        """Validate secret key meets security requirements."""
        if len(self.secret_key) < MIN_SECRET_LENGTH:
            print(f"⚠️  Security Warning: Secret key should be at least {MIN_SECRET_LENGTH} characters.")
            print(f"   Current length: {len(self.secret_key)} characters")

    def get_secret_info(self) -> dict[str, Any]:
        """Get information about the current secret key configuration.

        Returns:
            Information about secret source and strength.
        """
        return {
            "length": len(self.secret_key),
            "algorithm": self.algorithm,
            "is_strong": len(self.secret_key) >= MIN_SECRET_LENGTH,
        }

    def generate_token(self, expiration_date: datetime, user_uuid: str | None = None) -> tuple[str, str]:
        """Generate a JWT token.

        Args:
            expiration_date: Token expiration datetime.
            user_uuid: Optional UUID (auto-generated if not provided).

        Returns:
            Tuple of (token, user_uuid) where token is the JWT string.

        Raises:
            ValueError: If expiration_date is in the past.
            jwt.InvalidTokenError: If token generation fails.
        """
        user_uuid = user_uuid or str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Ensure timezone awareness
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)

        # Validate expiration is in the future
        if expiration_date <= now:
            error_message = "Expiration date must be in the future"
            raise ValueError(error_message)

        payload = {
            "sub": user_uuid,
            "iat": now,
            "exp": expiration_date,
            "iss": "ab-grid",  # Add issuer for better security
        }

        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        except Exception as e:
            error_message = f"Failed to generate token: {e}"
            raise jwt.InvalidTokenError(error_message) from e
        else:
            return token, user_uuid

    def verify_token(self, token: str) -> Any:
        """Verify and decode a JWT token.

        Args:
            token: The JWT token string to verify.

        Returns:
            Decoded token payload.

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired.
        """
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer="ab-grid"  # Verify issuer matches
            )
        except jwt.ExpiredSignatureError:
            error_message = "Token has expired"
            raise jwt.InvalidTokenError(error_message) from None
        except jwt.InvalidIssuerError:
            error_message = "Token issuer is invalid"
            raise jwt.InvalidTokenError(error_message) from None
        except Exception as e:
            error_message = f"Token verification failed: {e}"
            raise jwt.InvalidTokenError(error_message) from e

    def is_token_valid(self, token: str) -> bool:
        """Check if a token is valid without raising exceptions.

        Args:
            token: The JWT token string to check.

        Returns:
            True if token is valid, False otherwise.
        """
        try:
            self.verify_token(token)
        except jwt.InvalidTokenError:
            return False
        else:
            return True


    def get_token_info(self, token: str) -> dict[str, Any] | None:
        """Get information about a token without fully verifying it.

        Args:
            token: The JWT token string to analyze.

        Returns:
            Token information including expiration, subject, etc.
            None if token cannot be decoded.
        """
        try:
            # Decode without verification to get info
            unverified_payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )

            # Add additional computed fields
            exp_timestamp = unverified_payload.get("exp", 0)
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            is_expired = exp_datetime <= datetime.now(timezone.utc)

            return {
                "subject": unverified_payload.get("sub"),
                "issued_at": unverified_payload.get("iat"),
                "expires_at": exp_timestamp,
                "expires_at_datetime": exp_datetime.isoformat(),
                "issuer": unverified_payload.get("iss"),
                "is_expired": is_expired,
                "algorithm": self.algorithm,
            }
        except Exception:
            return None

def parse_expiration_date(date_string: str) -> datetime:
    """Parse date string to datetime with UTC timezone.

    Args:
        date_string: Date string in various supported formats.

    Returns:
        Parsed datetime with UTC timezone.

    Raises:
        SystemExit: If date string cannot be parsed.
    """
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_string, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    print(f"❌ Error parsing expiration date '{date_string}'.")
    print(f"   Supported formats: {', '.join(DATE_FORMATS[:3])}, etc.")
    sys.exit(1)

def validate_uuid(uuid_string: str) -> str:
    """Validate and normalize UUID string.

    Args:
        uuid_string: UUID string to validate.

    Returns:
        Normalized UUID string.

    Raises:
        SystemExit: If UUID string is invalid.
    """
    try:
        return str(uuid.UUID(uuid_string))
    except ValueError:
        print(f"❌ Invalid UUID: {uuid_string}")
        print("   Example: 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)

def save_token_data(
    token: str,
    expiration_date: datetime,
    user_uuid: str,
    output_path: Path,
    generator: JWTGenerator
) -> None:
    """Save JWT token and metadata to YAML file.

    Args:
        token: The JWT token string.
        expiration_date: Token expiration datetime.
        user_uuid: User UUID.
        output_path: Output file path.
        generator: JWTGenerator instance for additional info.
    """
    secret_info = generator.get_secret_info()

    data = {
        "jwt_token": token,
        "uuid": user_uuid,
        "expiration_date": expiration_date.isoformat(),
        "expiration_timestamp": int(expiration_date.timestamp()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": generator.algorithm,
        "secret_strength": "strong" if secret_info["is_strong"] else "weak",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(data, default_flow_style=False, indent=2))
    print(f"✅ JWT token saved to: {output_path}")

def show_configuration() -> None:
    """Display current environment configuration without creating a generator."""
    env_secret = os.getenv("AUTH_SECRET")
    algorithm = os.getenv("JWT_ALGORITHM", DEFAULT_ALGORITHM)

    config = {
        "AUTH_SECRET": "✅ Set in environment" if env_secret else "❌ Not set",
        "JWT_ALGORITHM": algorithm,
        "OUTPUT_DIRECTORY": str(DEFAULT_OUTPUT_DIR),
        "Min Secret Length": f"{MIN_SECRET_LENGTH} characters",
    }

    print("\nCURRENT ENVIRONMENT CONFIGURATION")
    print("=" * 50)
    for key, value in config.items():
        print(f"{key}: {value}")

    if env_secret:
        secret_length = len(env_secret)
        strength = "Strong" if secret_length >= MIN_SECRET_LENGTH else "Weak"
        print(f"Secret Length: {secret_length} characters ({strength})")
    else:
        print("\n⚠️  AUTH_SECRET is required to generate tokens.")
        print("   Set it in your .env file or as an environment variable.")

def create_parser() -> argparse.ArgumentParser:
    """Create and return argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Generate JWT token with expiration and UUID. Requires AUTH_SECRET to be configured.",
        epilog="Examples:\n"
               "  python create_jwt.py -e '2024-12-31' -u 'uuid-here'\n"
               "  python create_jwt.py --show-config",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-e", "--expiration",
                       help="Expiration date (required unless using --show-config or --token-info)")
    parser.add_argument("-u", "--uuid",
                       help="UUID (optional, auto-generated if not provided)")
    parser.add_argument("-o", "--output", type=Path,
                       help="Output file path (default: ./jwt_token.yaml)")
    parser.add_argument("-v", "--verify", action="store_true",
                       help="Verify generated token after creation")
    parser.add_argument("--show-config", action="store_true",
                       help="Show current configuration and exit")
    parser.add_argument("--token-info",
                       help="Show information about an existing token")
    return parser

def main() -> None:  # noqa: PLR0912, PLR0915
    """Main entry point for JWT token generation CLI."""
    args = create_parser().parse_args()

    # Handle configuration display (doesn't need secret key)
    if args.show_config:
        show_configuration()
        return

    # Handle token info display (needs secret for verification, but not for basic info)
    if args.token_info:
        # For token info, we can show basic info without secret, but need secret for verification
        print("\nTOKEN INFORMATION (Unverified)")
        print("=" * 50)

        try:
            # Decode without verification to get basic info
            unverified_payload = jwt.decode(
                args.token_info,
                options={"verify_signature": False, "verify_exp": False}
            )

            exp_timestamp = unverified_payload.get("exp", 0)
            exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            is_expired = exp_datetime <= datetime.now(timezone.utc)

            print(f"Subject: {unverified_payload.get('sub')}")
            print(f"Issued At: {unverified_payload.get('iat')}")
            print(f"Expires At: {exp_datetime.isoformat()}")
            print(f"Issuer: {unverified_payload.get('iss', 'Not set')}")
            print(f"Is Expired: {'Yes' if is_expired else 'No'}")

            # Try to verify if secret is available
            try:
                generator = JWTGenerator()
                if generator.is_token_valid(args.token_info):
                    print("Verification Status: ✅ Valid (signature verified)")
                else:
                    print("Verification Status: ❌ Invalid or expired")
            except SystemExit:
                print("Verification Status: ⚠️  Cannot verify (no secret key available)")

        except jwt.DecodeError:
            print("❌ Error: Invalid token format")
        except Exception as e:
            print(f"❌ Error: Could not decode token: {e}")

        return

    # Validate required arguments for token generation
    if not args.expiration:
        print("❌ Error: Expiration date required for token generation.")
        print("   Use --help for usage or --show-config to check configuration.")
        sys.exit(1)

    # Parse and validate expiration date
    expiration_date = parse_expiration_date(args.expiration)
    if expiration_date <= datetime.now(timezone.utc):
        print("❌ Error: Expiration date is in the past")
        sys.exit(1)

    # Prepare parameters
    user_uuid = validate_uuid(args.uuid) if args.uuid else None
    output_path = args.output or (DEFAULT_OUTPUT_DIR / "jwt_token.yaml")

    # Generate token (this will exit if no secret is available)
    generator = JWTGenerator()

    try:
        token, final_uuid = generator.generate_token(expiration_date, user_uuid)
        if not args.uuid:
            print(f"🔑 Generated UUID: {final_uuid}")
    except Exception as e:
        print(f"❌ Error generating JWT token: {e}")
        sys.exit(1)

    # Save to file
    save_token_data(token, expiration_date, final_uuid, output_path, generator)

    # Verify if requested
    if args.verify:
        try:
            decoded = generator.verify_token(token)
            print(f"✅ Token verified - Subject UUID: {decoded['sub']}")
        except jwt.InvalidTokenError as e:
            print(f"⚠️  Token verification failed: {e}")

    # Display summary
    secret_info = generator.get_secret_info()
    print("\nJWT TOKEN GENERATION SUMMARY")
    print("=" * 50)
    print(f"UUID: {final_uuid}")
    print(f"Expiration: {expiration_date}")
    print(f"Algorithm: {generator.algorithm}")
    print(f"Secret Strength: {'Strong' if secret_info['is_strong'] else 'Weak'}")
    print(f"Output: {output_path}")
    print(f"Token Length: {len(token)} characters")
    print(f"Token: {token}")
    print("=" * 50)

if __name__ == "__main__":
    main()
