from setuptools import setup, find_packages

setup(
    name="studypilot-shared",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "aio-pika>=9.0.0",
        "redis>=5.0.0",
    ],
)
