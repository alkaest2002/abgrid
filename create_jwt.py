import argparse
import jwt
import yaml
import uuid
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import sys

class JWTGenerator:
    def __init__(self, secret_key=None):
        load_dotenv()
        self.secret_key = secret_key or os.getenv("AUTH_SECRET", "default-secret-key")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        if self.secret_key == "default-secret-key":
            print("⚠️  Warning: Using default secret key. Configure AUTH_SECRET in .env for production.")

    def generate_token(self, expiration_date, user_uuid=None):
        user_uuid = user_uuid or str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        if expiration_date.tzinfo is None:
            expiration_date = expiration_date.replace(tzinfo=timezone.utc)
        payload = {"sub": user_uuid, "iat": now, "exp": expiration_date}
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, user_uuid

    def verify_token(self, token):
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

def parse_expiration_date(date_string):
    formats = [
        "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_string, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    print(f"❌ Error parsing expiration date. Supported formats: YYYY-MM-DD, YYYY-MM-DD HH:MM:SS, etc.")
    sys.exit(1)

def validate_uuid(uuid_string):
    try:
        return str(uuid.UUID(uuid_string))
    except ValueError:
        print(f"❌ Invalid UUID: {uuid_string}. Example UUID: 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)

def save_to_yaml(token, expiration_date, user_uuid, output_file, algorithm):
    data = {
        "jwt_token": token,
        "uuid": user_uuid,
        "expiration_date": expiration_date.isoformat(),
        "expiration_timestamp": int(expiration_date.timestamp()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": algorithm,
    }
    with open(output_file, "w") as file:
        yaml.dump(data, file, default_flow_style=False, indent=2)
    print(f"✅ JWT token saved to: {output_file}")

def load_env_config():
    load_dotenv()
    return {
        "JWT_SECRET_KEY": os.getenv("AUTH_SECRET", "default-secret-key"),
        "JWT_ALGORITHM": "HS256",
        "OUTPUT_DIRECTORY": "./",
    }

def main():
    parser = argparse.ArgumentParser(description="Generate JWT token with expiration and UUID using .env configuration.")
    parser.add_argument("-e", "--expiration", help="Expiration date (required unless using --show-config)")
    parser.add_argument("-u", "--uuid", help="UUID (optional, auto-generated if not provided)")
    parser.add_argument("-o", "--output", help="Output file name (default is jwt_token.yaml)")
    parser.add_argument("-s", "--secret", help="Secret key for JWT signing (overrides .env)")
    parser.add_argument("-v", "--verify", action="store_true", help="Verify generated token")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")
    args = parser.parse_args()

    if args.show_config:
        config = load_env_config()
        print("\nCURRENT ENVIRONMENT CONFIGURATION\n" + "="*50)
        for key, value in config.items():
            display_value = ("*" * 20 if key == "JWT_SECRET_KEY" else value)
            print(f"{key}: {display_value}")
        return

    if not args.expiration:
        print("❌ Error: Expiration date required. Use --help for usage.")
        sys.exit(1)

    config = load_env_config()
    expiration_date = parse_expiration_date(args.expiration)
    if expiration_date <= datetime.now(timezone.utc):
        if input("⚠️  Expiration date is in the past! Continue? (y/N): ").strip().lower() != "y":
            sys.exit(1)

    user_uuid = validate_uuid(args.uuid) if args.uuid else None

    output_file = args.output or os.path.join(config["OUTPUT_DIRECTORY"], "jwt_token.yaml")
    secret_key = args.secret or config["JWT_SECRET_KEY"]
    generator = JWTGenerator(secret_key)

    try:
        token, final_uuid = generator.generate_token(expiration_date, user_uuid)
        if not args.uuid:
            print(f"🔑 Generated UUID: {final_uuid}")
    except Exception as e:
        print(f"❌ Error generating JWT token: {e}")
        sys.exit(1)

    save_to_yaml(token, expiration_date, final_uuid, output_file, generator.algorithm)

    if args.verify:
        try:
            decoded = generator.verify_token(token)
            print(f"✅ Token verified: Subject UUID: {decoded.get("sub")}")
        except jwt.InvalidTokenError as e:
            print(f"⚠️  Token verification failed: {e}")

    print("\nJWT TOKEN GENERATION SUMMARY\n" + "="*50)
    print(f"UUID: {final_uuid}\nExpiration Date: {expiration_date}\nAlgorithm: {generator.algorithm}\nOutput File: {output_file}\nToken Length: {len(token)} characters\nToken: {token}\n" + "="*50)

if __name__ == "__main__":
    main()
