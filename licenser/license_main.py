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
DEFAULT_OUTPUT_DIR = Path("./licenser/licenses")
MIN_SECRET_LENGTH = 32
DATE_FORMATS = [
    "%Y-%m-%d", "%Y-%m-%d %H:%M",
    "%Y/%m/%d", "%Y/%m/%d %H:%M"
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

    def generate_token(self, expiration_date: datetime,) -> tuple[str, str]:
        """Generate a JWT token.

        Args:
            expiration_date: Token expiration datetime.

        Returns:
            Tuple of (token, user_uuid) where token is the JWT string.

        Raises:
            ValueError: If expiration_date is in the past.
            jwt.InvalidTokenError: If token generation fails.
        """
        user_uuid = str(uuid.uuid4())
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

def save_token_data(
    expiration_date: datetime,
    user_uuid: str,
    email: str,
    output_path: Path,
    generator: JWTGenerator
) -> None:
    """Save JWT token metadata to YAML file (without the JWT token itself).

    Args:
        expiration_date: Token expiration datetime.
        user_uuid: User UUID.
        email: User email address.
        output_path: Output file path.
        generator: JWTGenerator instance for additional info.
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
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(data, default_flow_style=False, indent=2))
    print(f"✅ Token data saved to: {output_path}")

def create_parser() -> argparse.ArgumentParser:
    """Create and return argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Generate JWT token with expiration and UUID. Requires AUTH_SECRET to be configured.",
        epilog="Examples:\n"
               "  python create_jwt.py -e user@example.com -x '2024-12-31'\n"
               "  python create_jwt.py --email user@example.com --expiration '2024-12-31'\n"
               "  python create_jwt.py --verify 'your.jwt.token.here'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Mutually exclusive group for main operations
    group = parser.add_mutually_exclusive_group(required=True)

    # Token generation arguments
    group.add_argument("--generate", action="store_true",
                      help="Generate a new JWT token (default action)")

    # Token verification argument
    group.add_argument("--verify",
                      help="Verify an existing JWT token")

    # Required arguments for token generation
    parser.add_argument("-e", "--email",
                       help="Email address (required for token generation)")
    parser.add_argument("-x", "--expiration",
                       help="Expiration date (required for token generation)")

    return parser

def main() -> None:  # noqa: PLR0915
    """Main entry point for JWT token generation CLI."""
    args = create_parser().parse_args()

    # Handle token verification
    if args.verify:
        try:
            generator = JWTGenerator()

            print("\nTOKEN VERIFICATION")
            print("=" * 50)

            try:
                decoded = generator.verify_token(args.verify)
                print("✅ Token is VALID")
                print(f"Subject UUID: {decoded.get('sub')}")
                exp_timestamp = decoded.get("exp", 0)
                exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                print(f"Expires At: {exp_datetime.isoformat()}")
                print(f"Issuer: {decoded.get('iss', 'Not set')}")

            except jwt.InvalidTokenError as e:
                print(f"❌ Token is INVALID: {e}")

                # Try to show basic info even for invalid tokens
                try:
                    unverified_payload = jwt.decode(
                        args.verify,
                        options={"verify_signature": False, "verify_exp": False}
                    )
                    print("\nToken Information (Unverified):")
                    print(f"Subject: {unverified_payload.get('sub')}")
                    exp_timestamp = unverified_payload.get("exp", 0)
                    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                    print(f"Expires At: {exp_datetime.isoformat()}")
                except Exception:
                    print("Could not decode token structure")

        except SystemExit:
            print("❌ Error: Cannot verify token (no secret key available)")

        return

    # Handle token generation (default action or explicit --generate)
    # Validate required arguments for token generation
    if not args.email:
        print("❌ Error: Email address required for token generation.")
        print("   Use --help for usage information.")
        sys.exit(1)

    if not args.expiration:
        print("❌ Error: Expiration date required for token generation.")
        print("   Use --help for usage information.")
        sys.exit(1)

    # Parse and validate expiration date
    expiration_date = parse_expiration_date(args.expiration)
    if expiration_date <= datetime.now(timezone.utc):
        print("❌ Error: Expiration date is in the past")
        sys.exit(1)

    # Generate token (this will exit if no secret is available)
    generator = JWTGenerator()

    try:
        token, final_uuid = generator.generate_token(expiration_date)
        print(f"🔑 Generated UUID: {final_uuid}")
    except Exception as e:
        print(f"❌ Error generating JWT token: {e}")
        sys.exit(1)

    # Create filename with email prefix
    safe_email = args.email.replace("@", "_at_").replace(".", "_")
    output_filename = f"{safe_email}_jwt_token.yaml"
    output_path = DEFAULT_OUTPUT_DIR / output_filename

    # Save to file (without the JWT token itself)
    save_token_data(expiration_date, final_uuid, args.email, output_path, generator)

    # Display summary
    secret_info = generator.get_secret_info()
    print("\nJWT TOKEN GENERATION SUMMARY")
    print("=" * 50)
    print(f"Email: {args.email}")
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
