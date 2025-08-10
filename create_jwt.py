"""JWT token generator with expiration and UUID support.

Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201

import argparse
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import jwt
import yaml
from dotenv import load_dotenv


# Load environment variables once at module level
load_dotenv()

# Configuration constants
DEFAULT_SECRET = "default-secret-key"
DEFAULT_ALGORITHM = "HS256"
DEFAULT_OUTPUT_DIR = Path("./")
DATE_FORMATS = [
    "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M",
]

class JWTGenerator:
    """Handles JWT token generation and verification."""

    def __init__(self, secret_key=None, algorithm=None):
        """Initialize JWT generator.

        Args:
            secret_key: Secret key for JWT signing (uses env var if not provided).
            algorithm: JWT algorithm (uses env var if not provided).
        """
        self.secret_key = secret_key or os.getenv("AUTH_SECRET", DEFAULT_SECRET)
        self.algorithm = algorithm or os.getenv("JWT_ALGORITHM", DEFAULT_ALGORITHM)

        if self.secret_key == DEFAULT_SECRET:
            print("⚠️  Warning: Using default secret key. Configure AUTH_SECRET in .env for production.")

    def generate_token(self, expiration_date, user_uuid=None):
        """Generate a JWT token.

        Args:
            expiration_date: Token expiration datetime.
            user_uuid: Optional UUID (auto-generated if not provided).

        Returns:
            Tuple of (token, user_uuid).
        """
        user_uuid = user_uuid or str(uuid.uuid4())
        now = datetime.now(datetime.UTC)

        # Ensure timezone awareness
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=datetime.UTC)

        payload = {
            "sub": user_uuid,
            "iat": now,
            "exp": expiration_date
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, user_uuid

    def verify_token(self, token):
        """Verify and decode a JWT token."""
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

def parse_expiration_date(date_string):
    """Parse date string to datetime with UTC timezone."""
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_string, fmt).replace(tzinfo=datetime.UTC)
        except ValueError:
            continue

    print(f"❌ Error parsing expiration date '{date_string}'.")
    print(f"   Supported formats: {', '.join(DATE_FORMATS[:3])}, etc.")
    sys.exit(1)

def validate_uuid(uuid_string):
    """Validate and normalize UUID string."""
    try:
        return str(uuid.UUID(uuid_string))
    except ValueError:
        print(f"❌ Invalid UUID: {uuid_string}")
        print("   Example: 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)

def save_token_data(token, expiration_date, user_uuid, output_path, algorithm):
    """Save JWT token and metadata to YAML file."""
    data = {
        "jwt_token": token,
        "uuid": user_uuid,
        "expiration_date": expiration_date.isoformat(),
        "expiration_timestamp": int(expiration_date.timestamp()),
        "generated_at": datetime.now(datetime.UTC).isoformat(),
        "algorithm": algorithm,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(data, default_flow_style=False, indent=2))
    print(f"✅ JWT token saved to: {output_path}")

def show_configuration():
    """Display current environment configuration."""
    config = {
        "AUTH_SECRET": os.getenv("AUTH_SECRET", DEFAULT_SECRET),
        "JWT_ALGORITHM": os.getenv("JWT_ALGORITHM", DEFAULT_ALGORITHM),
        "OUTPUT_DIRECTORY": DEFAULT_OUTPUT_DIR,
    }

    print("\nCURRENT ENVIRONMENT CONFIGURATION")
    print("=" * 50)
    for key, value in config.items():
        # Mask secret key for security
        display_value = "*" * 20 if key == "AUTH_SECRET" and value != DEFAULT_SECRET else value
        print(f"{key}: {display_value}")

def create_parser():
    """Create and return argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate JWT token with expiration and UUID using .env configuration."
    )
    parser.add_argument("-e", "--expiration",
                       help="Expiration date (required unless using --show-config)")
    parser.add_argument("-u", "--uuid",
                       help="UUID (optional, auto-generated if not provided)")
    parser.add_argument("-o", "--output", type=Path,
                       help="Output file path (default: ./jwt_token.yaml)")
    parser.add_argument("-s", "--secret",
                       help="Secret key for JWT signing (overrides .env)")
    parser.add_argument("-a", "--algorithm",
                       help="JWT algorithm (overrides .env)")
    parser.add_argument("-v", "--verify", action="store_true",
                       help="Verify generated token")
    parser.add_argument("--show-config", action="store_true",
                       help="Show current configuration")
    return parser

def main():
    """Main entry point for JWT token generation CLI."""
    args = create_parser().parse_args()

    # Handle configuration display
    if args.show_config:
        show_configuration()
        return

    # Validate required arguments
    if not args.expiration:
        print("❌ Error: Expiration date required. Use --help for usage.")
        sys.exit(1)

    # Parse and validate expiration date
    expiration_date = parse_expiration_date(args.expiration)
    if expiration_date <= datetime.now(datetime.UTC):
        print("⚠️  Expiration date is in the past!")
        sys.exit(1)

    # Prepare parameters
    user_uuid = validate_uuid(args.uuid) if args.uuid else None
    output_path = args.output or (DEFAULT_OUTPUT_DIR / "jwt_token.yaml")

    # Generate token
    generator = JWTGenerator(args.secret, args.algorithm)

    try:
        token, final_uuid = generator.generate_token(expiration_date, user_uuid)
        if not args.uuid:
            print(f"🔑 Generated UUID: {final_uuid}")
    except Exception as e:
        print(f"❌ Error generating JWT token: {e}")
        sys.exit(1)

    # Save to file
    save_token_data(token, expiration_date, final_uuid, output_path, generator.algorithm)

    # Verify if requested
    if args.verify:
        try:
            decoded = generator.verify_token(token)
            print(f"✅ Token verified - Subject UUID: {decoded['sub']}")
        except jwt.InvalidTokenError as e:
            print(f"⚠️  Token verification failed: {e}")

    # Display summary
    print("\nJWT TOKEN GENERATION SUMMARY")
    print("=" * 50)
    print(f"UUID: {final_uuid}")
    print(f"Expiration: {expiration_date}")
    print(f"Algorithm: {generator.algorithm}")
    print(f"Output: {output_path}")
    print(f"Token Length: {len(token)} characters")
    print(f"Token: {token}")
    print("=" * 50)

if __name__ == "__main__":
    main()
