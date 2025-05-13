import os
from setuptools import setup, find_packages

# Read the contents of the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read the requirements file
with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="stocker-pro",
    version="1.0.0",
    description="STOCKER Pro - Advanced stock analysis and portfolio management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="STOCKER Pro Team",
    author_email="team@stockerpro.com",
    url="https://github.com/yourusername/stocker-pro",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    entry_points={
        "console_scripts": [
            "stocker-api=stocker.interfaces.api.main:run_server",
        ],
    },
)
