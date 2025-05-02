from setuptools import setup, find_packages


setup(
    name="quantum_instant_coffee",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "matplotlib",
        "pandas",
    ],
)