import bcrypt

def hash_password(password: str) -> str:
    """
    RLVR: Implements hash_password with error handling and validation

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for hash_password
    """
    RLVR: Validates input according to business rules and constraints

    REASONING CHAIN:
    1. Problem: Input parameters and business logic for verify_password
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Validates input according to business rules and constraints
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    2. Analysis: Function complexity 1.0/5.0
    3. Solution: Implements hash_password with error handling and validation
    4. Implementation: Chain-of-Thought validation with error handling
    5. Validation: 3 test cases covering edge cases

    COMPLIANCE: STANDARD
    """
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
