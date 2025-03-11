from setuptools import setup, find_packages

with open("README.md", "r") as file:
    description = file.read()

setup(
    name='morsely',
    version='0.0.2',
    packages=find_packages(),
    install_requires=[
        'numpy>=2.1',
        'scipy>=1.15'
    ],
    long_description=description,
    long_description_content_type='text/markdown'
)