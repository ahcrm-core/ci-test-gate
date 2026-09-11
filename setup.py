from setuptools import setup, find_packages

setup(
    name="ci-test-gate",
    version="0.1.0",
    description="LLM-powered test selection for CI pipelines",
    author="Yunaremaia",
    author_email="yunare@gmail.com",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "click>=8.0",
        "pydantic>=2.0",
        "rich>=13.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ci-test-gate=ci_test_gate.cli:main",
        ],
    },
)
