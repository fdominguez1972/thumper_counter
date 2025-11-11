#!/usr/bin/env python3
"""
generate.py - Generate code from specifications using Claude API
Usage: python3 generate.py <spec_file> <prompt>
"""

import os
import sys
from pathlib import Path
from anthropic import Anthropic

# Initialize Anthropic client
# Set ANTHROPIC_API_KEY environment variable first
client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

def read_spec(spec_file):
    """Read specification file content"""
    with open(spec_file, 'r') as f:
        return f.read()

def generate_code(spec_content, prompt):
    """Generate code using Claude API"""
    system_prompt = """You are a code generator for the Thumper Counter project.
    Follow these rules:
    - Use ASCII-only output (no emojis or unicode)
    - Generate production-ready code
    - Include comprehensive comments
    - Follow the specifications exactly
    - Use Python 3.11+ features
    - Include type hints
    - Add docstrings for all functions/classes
    """
    
    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        temperature=0,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Specification:\n{spec_content}\n\nTask: {prompt}"
            }
        ]
    )
    
    return message.content[0].text

def main():
    if len(sys.argv) < 3:
        print("[FAIL] Usage: python3 generate.py <spec_file> <prompt>")
        print("Example: python3 generate.py specs/system.spec 'Create SQLAlchemy models'")
        sys.exit(1)
    
    spec_file = sys.argv[1]
    prompt = sys.argv[2]
    
    if not Path(spec_file).exists():
        print(f"[FAIL] Spec file not found: {spec_file}")
        sys.exit(1)
    
    print(f"[INFO] Reading spec: {spec_file}")
    spec_content = read_spec(spec_file)
    
    print(f"[INFO] Generating code with prompt: {prompt}")
    generated_code = generate_code(spec_content, prompt)
    
    print("[OK] Generated code:")
    print("=" * 50)
    print(generated_code)
    print("=" * 50)
    
    # Optionally save to file
    save = input("\nSave to file? (y/n): ")
    if save.lower() == 'y':
        filename = input("Enter filename: ")
        with open(filename, 'w') as f:
            f.write(generated_code)
        print(f"[OK] Saved to {filename}")

if __name__ == "__main__":
    main()
